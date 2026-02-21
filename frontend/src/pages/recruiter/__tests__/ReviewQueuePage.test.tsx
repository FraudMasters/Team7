/**
 * Tests for Recruiter ReviewQueuePage Component
 *
 * Tests the recruiter review queue page including:
 * - Displaying queue metrics (pending, urgent, avg wait, reviewed today, throughput)
 * - Search and filter functionality
 * - Candidate cards display
 * - Loading states
 * - Error states
 * - Empty states
 * - Navigation to candidate details
 * - Mobile-optimized layout
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReviewQueuePage } from '../ReviewQueuePage';

// Mock react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock recruiter data hooks
vi.mock('@/hooks/useRecruiterData', () => ({
  useRecruiterReviewQueue: vi.fn(() => ({
    data: {
      total_candidates: 15,
      candidates: [
        {
          id: 'cand-1',
          filename: 'john_doe_resume.pdf',
          candidate_name: 'John Doe',
          vacancy_id: 'vac-1',
          vacancy_title: 'Senior Developer',
          current_stage: 'screening',
          stage_name: 'Screening',
          priority: 'urgent',
          days_in_stage: 5,
          match_score: 0.85,
          recruiter_feedback: [
            {
              recruiter_name: 'Alice Smith',
              rating: 4,
              recommendation: 'approve',
              notes: 'Strong technical background',
              created_at: '2024-01-15T10:00:00Z',
            },
          ],
          team_consensus: 'approve',
          tags: ['python', 'react'],
          assigned_recruiter_id: 'rec-1',
          assigned_recruiter_name: 'Alice Smith',
          created_at: '2024-01-10T10:00:00Z',
          updated_at: '2024-01-15T10:00:00Z',
        },
        {
          id: 'cand-2',
          filename: 'jane_smith_resume.pdf',
          candidate_name: 'Jane Smith',
          vacancy_id: 'vac-2',
          vacancy_title: 'Product Manager',
          current_stage: 'interview',
          stage_name: 'Interview',
          priority: 'high',
          days_in_stage: 3,
          match_score: 0.72,
          recruiter_feedback: [],
          team_consensus: 'mixed',
          tags: ['agile', 'leadership'],
          assigned_recruiter_id: null,
          assigned_recruiter_name: null,
          created_at: '2024-01-12T10:00:00Z',
          updated_at: '2024-01-15T10:00:00Z',
        },
        {
          id: 'cand-3',
          filename: 'bob_jones_resume.pdf',
          candidate_name: 'Bob Jones',
          vacancy_id: 'vac-1',
          vacancy_title: 'Senior Developer',
          current_stage: 'screening',
          stage_name: 'Screening',
          priority: 'normal',
          days_in_stage: 2,
          match_score: null,
          recruiter_feedback: [],
          team_consensus: null,
          tags: [],
          assigned_recruiter_id: null,
          assigned_recruiter_name: null,
          created_at: '2024-01-13T10:00:00Z',
          updated_at: '2024-01-15T10:00:00Z',
        },
      ],
      metrics: {
        total_pending: 15,
        urgent_count: 3,
        avg_wait_days: 4.2,
        reviewed_today: 7,
        throughput_week: 28,
      },
      filters_applied: {},
      pagination: {
        skip: 0,
        limit: 50,
        total: 15,
      },
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  })),
}));

// Mock LoadingSpinner component
vi.mock('@/components/LoadingSpinner', () => ({
  default: ({ message }: { message?: string }) => (
    <div data-testid="loading-spinner">
      {message || 'Loading...'}
    </div>
  ),
}));

// Create a new query client for each test
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderWithProviders = (component: React.ReactNode) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{component}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Recruiter ReviewQueuePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Page Header', () => {
    it('should render the page title', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Review Queue')).toBeInTheDocument();
    });

    it('should render the subtitle', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(
        screen.getByText('Prioritized candidates awaiting your review')
      ).toBeInTheDocument();
    });

    it('should display title as h4', () => {
      renderWithProviders(<ReviewQueuePage />);

      const title = screen.getByRole('heading', { level: 4 });
      expect(title).toHaveTextContent('Review Queue');
    });

    it('should render refresh button', () => {
      renderWithProviders(<ReviewQueuePage />);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      expect(refreshButton).toBeInTheDocument();
    });
  });

  describe('Metrics Display', () => {
    it('should display pending count', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Pending')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
    });

    it('should display urgent count', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Urgent')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('should display average wait time', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Avg Wait')).toBeInTheDocument();
      expect(screen.getByText('4.2d')).toBeInTheDocument();
    });

    it('should display reviewed today count', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Reviewed Today')).toBeInTheDocument();
      expect(screen.getByText('7')).toBeInTheDocument();
    });

    it('should display weekly throughput', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Weekly Throughput')).toBeInTheDocument();
      expect(screen.getByText('28')).toBeInTheDocument();
    });
  });

  describe('Search and Filter', () => {
    it('should render search input', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByPlaceholderText('Search candidates...')).toBeInTheDocument();
    });

    it('should render filters button', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Filters')).toBeInTheDocument();
    });

    it('should show candidate count', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText(/15.*candidates/)).toBeInTheDocument();
    });

    it('should toggle filter panel when clicking Filters button', () => {
      renderWithProviders(<ReviewQueuePage />);

      // Initially, vacancy filter is not visible
      expect(screen.queryByText('Vacancy')).not.toBeInTheDocument();

      // Click Filters button
      fireEvent.click(screen.getByText('Filters'));

      // Now vacancy filter should be visible
      expect(screen.getByText('Vacancy')).toBeInTheDocument();
    });

    it('should show priority filter when filters expanded', () => {
      renderWithProviders(<ReviewQueuePage />);

      fireEvent.click(screen.getByText('Filters'));

      expect(screen.getByText('Priority')).toBeInTheDocument();
    });

    it('should show clear all button when filters active', async () => {
      renderWithProviders(<ReviewQueuePage />);

      // Type in search to activate filter
      const searchInput = screen.getByPlaceholderText('Search candidates...');
      fireEvent.change(searchInput, { target: { value: 'John' } });

      // Clear All button should appear
      expect(screen.getByText('Clear All')).toBeInTheDocument();
    });

    it('should clear all filters when clicking Clear All', () => {
      renderWithProviders(<ReviewQueuePage />);

      // Type in search
      const searchInput = screen.getByPlaceholderText('Search candidates...');
      fireEvent.change(searchInput, { target: { value: 'John' } });

      // Click Clear All
      fireEvent.click(screen.getByText('Clear All'));

      // Search should be cleared
      expect(searchInput).toHaveValue('');
    });
  });

  describe('Candidate Cards', () => {
    it('should display candidate cards', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
      expect(screen.getByText('Bob Jones')).toBeInTheDocument();
    });

    it('should display candidate vacancy title', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Senior Developer')).toBeInTheDocument();
      expect(screen.getByText('Product Manager')).toBeInTheDocument();
    });

    it('should display priority badge for urgent candidates', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('URGENT')).toBeInTheDocument();
    });

    it('should display stage chip', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Screening')).toBeInTheDocument();
      expect(screen.getByText('Interview')).toBeInTheDocument();
    });

    it('should display days in stage', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText(/5d/)).toBeInTheDocument();
      expect(screen.getByText(/3d/)).toBeInTheDocument();
    });

    it('should display match score when available', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('85%')).toBeInTheDocument();
      expect(screen.getByText('72%')).toBeInTheDocument();
    });

    it('should display assigned recruiter', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Assigned to')).toBeInTheDocument();
      expect(screen.getByText('Alice Smith')).toBeInTheDocument();
    });

    it('should display team consensus', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Team Consensus')).toBeInTheDocument();
      expect(screen.getByText('Approve')).toBeInTheDocument();
      expect(screen.getByText('Mixed')).toBeInTheDocument();
    });

    it('should display recruiter feedback', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('Recruiter Feedback')).toBeInTheDocument();
      expect(screen.getByText('Strong technical background')).toBeInTheDocument();
    });

    it('should display tags', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText('python')).toBeInTheDocument();
      expect(screen.getByText('react')).toBeInTheDocument();
      expect(screen.getByText('agile')).toBeInTheDocument();
    });

    it('should display View Details button for each candidate', () => {
      renderWithProviders(<ReviewQueuePage />);

      const viewButtons = screen.getAllByText('View Details');
      expect(viewButtons).toHaveLength(3);
    });

    it('should navigate to candidate details when clicking View Details', () => {
      renderWithProviders(<ReviewQueuePage />);

      const viewButtons = screen.getAllByText('View Details');
      fireEvent.click(viewButtons[0]);

      expect(mockNavigate).toHaveBeenCalledWith('/recruiter/candidates/cand-1');
    });
  });

  describe('Layout and Responsive Design', () => {
    it('should use Container component with maxWidth xl', () => {
      const { container } = renderWithProviders(<ReviewQueuePage />);

      const containers = container.querySelectorAll('.MuiContainer-maxWidthXl');
      expect(containers.length).toBeGreaterThan(0);
    });

    it('should use Grid components for candidate cards layout', () => {
      const { container } = renderWithProviders(<ReviewQueuePage />);

      const grids = container.querySelectorAll('.MuiGrid-root');
      expect(grids.length).toBeGreaterThan(0);
    });
  });

  describe('Tip Section', () => {
    it('should display tip section at bottom', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(screen.getByText(/Tip:/)).toBeInTheDocument();
    });

    it('should display tip content about priority sorting', () => {
      renderWithProviders(<ReviewQueuePage />);

      expect(
        screen.getByText(
          /Candidates are sorted by priority/
        )
      ).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      renderWithProviders(<ReviewQueuePage />);

      // Main title is h4
      const h4 = screen.getByRole('heading', { level: 4 });
      expect(h4).toBeInTheDocument();
    });

    it('should have accessible buttons', () => {
      renderWithProviders(<ReviewQueuePage />);

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should have touch-friendly button targets (44px min height)', () => {
      const { container } = renderWithProviders(<ReviewQueuePage />);

      const viewButtons = container.querySelectorAll('.MuiButton-root');
      viewButtons.forEach((button) => {
        // View Details buttons should have 44px minimum height
        if (button.textContent?.includes('View Details')) {
          expect(button).toHaveStyle({ minHeight: '44px' });
        }
      });
    });
  });
});

describe('Recruiter ReviewQueuePage - Loading State', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Override the mock for loading state
    vi.mocked(require('@/hooks/useRecruiterData').useRecruiterReviewQueue).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });
  });

  it('should display loading spinner', () => {
    renderWithProviders(<ReviewQueuePage />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('should display loading message', () => {
    renderWithProviders(<ReviewQueuePage />);

    expect(screen.getByText('Loading candidates...')).toBeInTheDocument();
  });
});

describe('Recruiter ReviewQueuePage - Error State', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Override the mock for error state
    vi.mocked(require('@/hooks/useRecruiterData').useRecruiterReviewQueue).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    });
  });

  it('should display error title', () => {
    renderWithProviders(<ReviewQueuePage />);

    expect(screen.getByText('Failed to load candidates')).toBeInTheDocument();
  });

  it('should display error message', () => {
    renderWithProviders(<ReviewQueuePage />);

    expect(
      screen.getByText('Please try again or contact support if the problem persists.')
    ).toBeInTheDocument();
  });

  it('should display retry button', () => {
    renderWithProviders(<ReviewQueuePage />);

    expect(screen.getByText('Retry')).toBeInTheDocument();
  });
});

describe('Recruiter ReviewQueuePage - Empty State', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display empty state when no candidates', () => {
    vi.mocked(require('@/hooks/useRecruiterData').useRecruiterReviewQueue).mockReturnValue({
      data: {
        total_candidates: 0,
        candidates: [],
        metrics: {
          total_pending: 0,
          urgent_count: 0,
          avg_wait_days: 0,
          reviewed_today: 0,
          throughput_week: 0,
        },
        filters_applied: {},
        pagination: {
          skip: 0,
          limit: 50,
          total: 0,
        },
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    renderWithProviders(<ReviewQueuePage />);

    expect(screen.getByText('No candidates pending review')).toBeInTheDocument();
    expect(
      screen.getByText('All caught up! New candidates will appear here when they need your review.')
    ).toBeInTheDocument();
  });

  it('should display no matches state when filters applied but no results', () => {
    vi.mocked(require('@/hooks/useRecruiterData').useRecruiterReviewQueue).mockReturnValue({
      data: {
        total_candidates: 0,
        candidates: [],
        metrics: {
          total_pending: 0,
          urgent_count: 0,
          avg_wait_days: 0,
          reviewed_today: 0,
          throughput_week: 0,
        },
        filters_applied: { search: 'NonexistentName' },
        pagination: {
          skip: 0,
          limit: 50,
          total: 0,
        },
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    // Render with search term to simulate active filters
    const { rerender } = renderWithProviders(<ReviewQueuePage />);

    // Type in search to simulate filter being active
    const searchInput = screen.getByPlaceholderText('Search candidates...');
    fireEvent.change(searchInput, { target: { value: 'NonexistentName' } });

    rerender(
      <QueryClientProvider client={createTestQueryClient()}>
        <BrowserRouter>
          <ReviewQueuePage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText('No candidates match your filters')).toBeInTheDocument();
    expect(screen.getByText('Try adjusting your search criteria')).toBeInTheDocument();
  });
});

describe('Recruiter ReviewQueuePage - Pagination', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display pagination info when total exceeds limit', () => {
    vi.mocked(require('@/hooks/useRecruiterData').useRecruiterReviewQueue).mockReturnValue({
      data: {
        total_candidates: 100,
        candidates: Array.from({ length: 50 }, (_, i) => ({
          id: `cand-${i}`,
          filename: `candidate_${i}_resume.pdf`,
          candidate_name: `Candidate ${i}`,
          vacancy_id: 'vac-1',
          vacancy_title: 'Senior Developer',
          current_stage: 'screening',
          stage_name: 'Screening',
          priority: 'normal',
          days_in_stage: 2,
          match_score: null,
          recruiter_feedback: [],
          team_consensus: null,
          tags: [],
          assigned_recruiter_id: null,
          assigned_recruiter_name: null,
          created_at: '2024-01-10T10:00:00Z',
          updated_at: '2024-01-15T10:00:00Z',
        })),
        metrics: {
          total_pending: 100,
          urgent_count: 5,
          avg_wait_days: 3.5,
          reviewed_today: 10,
          throughput_week: 35,
        },
        filters_applied: {},
        pagination: {
          skip: 0,
          limit: 50,
          total: 100,
        },
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    renderWithProviders(<ReviewQueuePage />);

    expect(screen.getByText(/Showing 50 of 100 candidates/)).toBeInTheDocument();
  });

  it('should not display pagination info when total is within limit', () => {
    vi.mocked(require('@/hooks/useRecruiterData').useRecruiterReviewQueue).mockReturnValue({
      data: {
        total_candidates: 15,
        candidates: Array.from({ length: 15 }, (_, i) => ({
          id: `cand-${i}`,
          filename: `candidate_${i}_resume.pdf`,
          candidate_name: `Candidate ${i}`,
          vacancy_id: 'vac-1',
          vacancy_title: 'Senior Developer',
          current_stage: 'screening',
          stage_name: 'Screening',
          priority: 'normal',
          days_in_stage: 2,
          match_score: null,
          recruiter_feedback: [],
          team_consensus: null,
          tags: [],
          assigned_recruiter_id: null,
          assigned_recruiter_name: null,
          created_at: '2024-01-10T10:00:00Z',
          updated_at: '2024-01-15T10:00:00Z',
        })),
        metrics: {
          total_pending: 15,
          urgent_count: 2,
          avg_wait_days: 2.5,
          reviewed_today: 5,
          throughput_week: 20,
        },
        filters_applied: {},
        pagination: {
          skip: 0,
          limit: 50,
          total: 15,
        },
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    renderWithProviders(<ReviewQueuePage />);

    expect(screen.queryByText(/Showing/)).not.toBeInTheDocument();
  });
});
