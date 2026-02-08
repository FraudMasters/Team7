/**
 * Tests for JobsBrowsePage Component - Exclude Skills Filter
 *
 * Tests the tech stack exclusion filter including:
 * - Filtering out jobs with excluded skills
 * - Case-insensitive skill matching
 * - Empty excluded list behavior
 * - localStorage persistence
 * - Clear button functionality
 * - Duplicate prevention
 * - Empty state handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { JobsBrowsePage } from './JobsBrowsePage';
import * as useJobsHook from '../../hooks/useJobs';

// Mock the useJobs hook
vi.mock('../../hooks/useJobs');

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'jobsBrowse.excludeStacks.title': "Don't show jobs with these skills",
        'jobsBrowse.excludeStacks.placeholder': 'Enter technologies to exclude...',
        'jobsBrowse.excludeStacks.clear': 'Clear filters',
        'jobsBrowse.excludeStacks.noFilteredJobs': 'All jobs are hidden by your filters',
      };
      return translations[key] || key;
    },
  }),
}));

describe('JobsBrowsePage - Exclude Skills Filter', () => {
  const mockVacancies = [
    {
      id: '1',
      title: 'React Developer',
      description: 'Frontend role',
      required_skills: ['React', 'TypeScript', 'JavaScript'],
      min_experience_months: 24,
      work_format: 'remote' as const,
    },
    {
      id: '2',
      title: 'Java Backend Developer',
      description: 'Backend role',
      required_skills: ['Java', 'Spring', 'PostgreSQL'],
      min_experience_months: 36,
      work_format: 'office' as const,
    },
    {
      id: '3',
      title: 'Python Developer',
      description: 'Full stack role',
      required_skills: ['Python', 'Django', 'React'],
      min_experience_months: 12,
      work_format: 'hybrid' as const,
    },
  ];

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
        {children}
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Clear localStorage before each test
    localStorage.clear();

    // Mock useJobs hook to return data
    vi.mocked(useJobsHook.useJobs).mockReturnValue({
      data: { vacancies: mockVacancies, total: 3 },
      isLoading: false,
      error: null,
    } as any);
  });

  describe('Filter Functionality', () => {
    it('filters out jobs with excluded skills', async () => {
      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // All jobs should be visible initially
      expect(screen.getByText('React Developer')).toBeInTheDocument();
      expect(screen.getByText('Java Backend Developer')).toBeInTheDocument();
      expect(screen.getByText('Python Developer')).toBeInTheDocument();

      // Find the autocomplete input
      const autocompleteInput = screen.getByLabelText(/don't show jobs with these skills/i);

      // Type 'Java' and select it
      fireEvent.change(autocompleteInput, { target: { value: 'Java' } });

      // Wait for options to appear and click the first one
      await waitFor(() => {
        const option = screen.getByText('Java');
        fireEvent.click(option);
      });

      // Wait for the chip to appear and filtering to happen
      await waitFor(() => {
        // Java job should NOT be displayed
        expect(screen.queryByText('Java Backend Developer')).not.toBeInTheDocument();
        // React and Python jobs should still be displayed
        expect(screen.getByText('React Developer')).toBeInTheDocument();
        expect(screen.getByText('Python Developer')).toBeInTheDocument();
      });
    });

    it('performs case-insensitive matching', async () => {
      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // All jobs should be visible initially
      expect(screen.getByText('React Developer')).toBeInTheDocument();

      // Find the autocomplete input
      const autocompleteInput = screen.getByLabelText(/don't show jobs with these skills/i);

      // Type 'react' (lowercase) and select it
      fireEvent.change(autocompleteInput, { target: { value: 'react' } });

      // Wait for options to appear and click React
      await waitFor(() => {
        const option = screen.getByText('React');
        fireEvent.click(option);
      });

      // Wait for filtering - 'React' (capitalized) job should be excluded
      await waitFor(() => {
        expect(screen.queryByText('React Developer')).not.toBeInTheDocument();
      });
    });

    it('shows all jobs when no skills excluded', () => {
      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // Without any exclusions, verify all 3 jobs are displayed
      expect(screen.getByText('React Developer')).toBeInTheDocument();
      expect(screen.getByText('Java Backend Developer')).toBeInTheDocument();
      expect(screen.getByText('Python Developer')).toBeInTheDocument();

      // Count Developer occurrences (3 jobs)
      const developerTexts = screen.getAllByText(/developer/i);
      expect(developerTexts).toHaveLength(3);
    });
  });

  describe('localStorage Persistence', () => {
    it('persists excluded skills to localStorage', async () => {
      const setItemSpy = vi.spyOn(Storage.prototype, 'setItem');

      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // Find the autocomplete input
      const autocompleteInput = screen.getByLabelText(/don't show jobs with these skills/i);

      // Type 'Java' and select it
      fireEvent.change(autocompleteInput, { target: { value: 'Java' } });

      await waitFor(() => {
        const option = screen.getByText('Java');
        fireEvent.click(option);
      });

      // Wait for localStorage to be updated
      await waitFor(() => {
        expect(setItemSpy).toHaveBeenCalledWith(
          'excludedJobSkills',
          JSON.stringify(['Java'])
        );
      });

      setItemSpy.mockRestore();
    });

    it('loads excluded skills from localStorage on mount', () => {
      // Pre-populate localStorage
      localStorage.setItem('excludedJobSkills', JSON.stringify(['Java']));

      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // Verify 'Java' job is NOT displayed (loaded from localStorage)
      expect(screen.queryByText('Java Backend Developer')).not.toBeInTheDocument();

      // Verify other jobs ARE displayed
      expect(screen.getByText('React Developer')).toBeInTheDocument();
      expect(screen.getByText('Python Developer')).toBeInTheDocument();

      // Verify the chip is shown
      expect(screen.getByText('Java')).toBeInTheDocument();
    });
  });

  describe('Clear Button', () => {
    it('clears all excluded skills when clear button clicked', async () => {
      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // Find the autocomplete input
      const autocompleteInput = screen.getByLabelText(/don't show jobs with these skills/i);

      // Add 'Java' to excluded skills
      fireEvent.change(autocompleteInput, { target: { value: 'Java' } });

      await waitFor(() => {
        const option = screen.getByText('Java');
        fireEvent.click(option);
      });

      // Wait for the chip to appear
      await waitFor(() => {
        expect(screen.getByText('Java')).toBeInTheDocument();
      });

      // Find and click the clear button
      const clearButton = screen.getByRole('button', { name: /clear filters/i });
      fireEvent.click(clearButton);

      // Wait for all jobs to become visible again
      await waitFor(() => {
        expect(screen.getByText('Java Backend Developer')).toBeInTheDocument();
        expect(screen.getByText('React Developer')).toBeInTheDocument();
        expect(screen.getByText('Python Developer')).toBeInTheDocument();
      });

      // Verify the chip is removed
      expect(screen.queryByText('Java')).not.toBeInTheDocument();
    });
  });

  describe('Duplicate Prevention', () => {
    it('prevents duplicate skills in exclusion list', async () => {
      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // Find the autocomplete input
      const autocompleteInput = screen.getByLabelText(/don't show jobs with these skills/i);

      // Add 'Java' to excluded skills
      fireEvent.change(autocompleteInput, { target: { value: 'Java' } });

      await waitFor(() => {
        const option = screen.getByText('Java');
        fireEvent.click(option);
      });

      // Wait for the chip to appear
      await waitFor(() => {
        expect(screen.getByText('Java')).toBeInTheDocument();
      });

      // Try to add 'Java' again
      fireEvent.change(autocompleteInput, { target: { value: 'Java' } });

      await waitFor(() => {
        const option = screen.getByText('Java');
        fireEvent.click(option);
      });

      // Verify only one 'Java' chip appears
      await waitFor(() => {
        const javaChips = screen.getAllByText('Java');
        expect(javaChips.length).toBe(1);
      });
    });
  });

  describe('Empty State', () => {
    it('shows empty state message when all jobs filtered', async () => {
      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // Find the autocomplete input
      const autocompleteInput = screen.getByLabelText(/don't show jobs with these skills/i);

      // Add skills to exclude all jobs (React, Java, Python)
      fireEvent.change(autocompleteInput, { target: { value: 'React' } });

      await waitFor(() => {
        const option = screen.getByText('React');
        fireEvent.click(option);
      });

      // Add Java
      fireEvent.change(autocompleteInput, { target: { value: 'Java' } });

      await waitFor(() => {
        const option = screen.getByText('Java');
        fireEvent.click(option);
      });

      // Add Python
      fireEvent.change(autocompleteInput, { target: { value: 'Python' } });

      await waitFor(() => {
        const option = screen.getByText('Python');
        fireEvent.click(option);
      });

      // Wait for empty state message
      await waitFor(() => {
        expect(screen.getByText('All jobs are hidden by your filters')).toBeInTheDocument();
      });

      // Verify no jobs are displayed
      expect(screen.queryByText('React Developer')).not.toBeInTheDocument();
      expect(screen.queryByText('Java Backend Developer')).not.toBeInTheDocument();
      expect(screen.queryByText('Python Developer')).not.toBeInTheDocument();
    });
  });

  describe('Integration with Existing Filters', () => {
    it('works correctly with search filter', async () => {
      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // Add search term
      const searchInput = screen.getByPlaceholderText('Search jobs...');
      fireEvent.change(searchInput, { target: { value: 'Developer' } });

      // All Developer jobs should be visible
      expect(screen.getByText('React Developer')).toBeInTheDocument();
      expect(screen.getByText('Java Backend Developer')).toBeInTheDocument();
      expect(screen.getByText('Python Developer')).toBeInTheDocument();

      // Now exclude 'Java'
      const autocompleteInput = screen.getByLabelText(/don't show jobs with these skills/i);
      fireEvent.change(autocompleteInput, { target: { value: 'Java' } });

      await waitFor(() => {
        const option = screen.getByText('Java');
        fireEvent.click(option);
      });

      // Wait for filtering
      await waitFor(() => {
        // Java job should NOT be displayed
        expect(screen.queryByText('Java Backend Developer')).not.toBeInTheDocument();
        // React and Python jobs should still be displayed
        expect(screen.getByText('React Developer')).toBeInTheDocument();
        expect(screen.getByText('Python Developer')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles partial skill matching correctly', async () => {
      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // All jobs should be visible initially
      expect(screen.getByText('React Developer')).toBeInTheDocument();

      // Find the autocomplete input
      const autocompleteInput = screen.getByLabelText(/don't show jobs with these skills/i);

      // Exclude 'Script' which partially matches 'JavaScript' and 'TypeScript'
      fireEvent.change(autocompleteInput, { target: { value: 'Script' } });

      await waitFor(() => {
        const option = screen.getByText('Script'); // Assuming 'Script' is in skillOptions
        if (option) {
          fireEvent.click(option);
        }
      });

      // React Developer requires JavaScript and TypeScript
      // Both contain 'Script', so the job should be excluded
      await waitFor(() => {
        expect(screen.queryByText('React Developer')).not.toBeInTheDocument();
      });
    });

    it('handles removing individual skills via chip delete', async () => {
      render(<JobsBrowsePage />, { wrapper: createWrapper() });

      // Find the autocomplete input
      const autocompleteInput = screen.getByLabelText(/don't show jobs with these skills/i);

      // Add two skills
      fireEvent.change(autocompleteInput, { target: { value: 'Java' } });

      await waitFor(() => {
        const option = screen.getByText('Java');
        fireEvent.click(option);
      });

      fireEvent.change(autocompleteInput, { target: { value: 'Python' } });

      await waitFor(() => {
        const option = screen.getByText('Python');
        fireEvent.click(option);
      });

      // Wait for chips to appear
      await waitFor(() => {
        expect(screen.getByText('Java')).toBeInTheDocument();
        expect(screen.getByText('Python')).toBeInTheDocument();
      });

      // Both jobs should be filtered out
      expect(screen.queryByText('Java Backend Developer')).not.toBeInTheDocument();
      expect(screen.queryByText('Python Developer')).not.toBeInTheDocument();

      // Click the delete button on Java chip
      const javaChips = screen.getAllByText('Java');
      const javaChip = javaChips[0];
      const deleteButton = javaChip.parentElement?.querySelector('button');

      if (deleteButton) {
        fireEvent.click(deleteButton);

        // Java job should reappear
        await waitFor(() => {
          expect(screen.getByText('Java Backend Developer')).toBeInTheDocument();
        });

        // Python should still be filtered
        expect(screen.queryByText('Python Developer')).not.toBeInTheDocument();
      }
    });
  });
});
