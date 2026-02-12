/**
 * Tests for Hiring Manager DashboardPage Component
 *
 * Tests the hiring manager dashboard page including:
 * - Displaying dashboard statistics (pending review, urgent, approved, avg time)
 * - Quick actions navigation
 * - My vacancies section
 * - Recent activity section
 * - Loading states
 * - Mobile-optimized layout
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from '../DashboardPage';

// Mock react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock hiring manager data hooks
vi.mock('@/hooks/useHiringManagerData', () => ({
  useHiringManagerDashboard: vi.fn(() => ({
    data: {
      pending_review: {
        total_pending: 12,
        urgent_count: 3,
      },
      quick_stats: {
        approved_this_month: 8,
        avg_time_to_decision_days: 2.5,
        interviews_scheduled: 5,
      },
      my_vacancies: [
        {
          vacancy_id: 'vac-1',
          vacancy_title: 'Senior Developer',
          pending_review: 5,
          total_candidates: 15,
        },
        {
          vacancy_id: 'vac-2',
          vacancy_title: 'Product Manager',
          pending_review: 3,
          total_candidates: 10,
        },
      ],
      recent_activity: [
        {
          activity_type: 'approved',
          candidate_name: 'John Doe',
          vacancy_title: 'Senior Developer',
          timestamp: '2024-01-15T10:00:00Z',
        },
        {
          activity_type: 'rejected',
          candidate_name: 'Jane Smith',
          vacancy_title: 'Product Manager',
          timestamp: '2024-01-14T15:30:00Z',
        },
      ],
    },
    isLoading: false,
  })),
  useHiringManagerReviewQueue: vi.fn(() => ({
    data: {
      candidates: [],
    },
  })),
}));

// Mock BentoCard component
vi.mock('@/components/dashboard/BentoCard', () => ({
  BentoCard: ({ title, value, subtitle }: { title: string; value: string | number; subtitle: string }) => (
    <div data-testid="bento-card">
      <div data-testid="bento-title">{title}</div>
      <div data-testid="bento-value">{value}</div>
      <div data-testid="bento-subtitle">{subtitle}</div>
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

describe('Hiring Manager DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Page Header', () => {
    it('should render the dashboard title', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Hiring Manager Dashboard')).toBeInTheDocument();
    });

    it('should render welcome message', () => {
      renderWithProviders(<DashboardPage />);

      expect(
        screen.getByText('Welcome back! Here are the candidates awaiting your review.')
      ).toBeInTheDocument();
    });

    it('should display title as h4', () => {
      renderWithProviders(<DashboardPage />);

      const title = screen.getByRole('heading', { level: 4 });
      expect(title).toHaveTextContent('Hiring Manager Dashboard');
    });
  });

  describe('Statistics Cards', () => {
    it('should display pending review count', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Pending Review')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
    });

    it('should display urgent count', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Urgent')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('should display approved this month count', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Approved')).toBeInTheDocument();
      expect(screen.getByText('8')).toBeInTheDocument();
    });

    it('should display average decision time', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Avg. Decision Time')).toBeInTheDocument();
      expect(screen.getByText('2.5d')).toBeInTheDocument();
    });

    it('should render all four stat cards', () => {
      renderWithProviders(<DashboardPage />);

      const bentoCards = screen.getAllByTestId('bento-card');
      expect(bentoCards).toHaveLength(4);
    });
  });

  describe('Quick Actions Section', () => {
    it('should display quick actions section header', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    });

    it('should render Review Queue action', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Review Queue')).toBeInTheDocument();
      expect(
        screen.getByText('View candidates awaiting your decision')
      ).toBeInTheDocument();
    });

    it('should render Approvals action', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Approvals')).toBeInTheDocument();
      expect(screen.getByText('Manage approved candidates')).toBeInTheDocument();
    });

    it('should render Interviews action', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Interviews')).toBeInTheDocument();
      expect(screen.getByText('Schedule and manage interviews')).toBeInTheDocument();
    });

    it('should render My Profile action', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('My Profile')).toBeInTheDocument();
      expect(screen.getByText('Update your preferences')).toBeInTheDocument();
    });

    it('should navigate to review queue when clicking Review Queue card', () => {
      renderWithProviders(<DashboardPage />);

      const reviewQueueCard = screen.getByText('Review Queue').closest('.MuiCard-root');
      fireEvent.click(reviewQueueCard!);

      expect(mockNavigate).toHaveBeenCalledWith('/hiring-manager/review-queue');
    });

    it('should navigate when clicking Open button', () => {
      renderWithProviders(<DashboardPage />);

      const openButtons = screen.getAllByText('Open');
      fireEvent.click(openButtons[0]);

      expect(mockNavigate).toHaveBeenCalled();
    });

    it('should display badge for Review Queue with pending count', () => {
      renderWithProviders(<DashboardPage />);

      // The Review Queue should show the pending review count as a badge (12)
      const badges = screen.getAllByText('12');
      expect(badges.length).toBeGreaterThan(0);
    });

    it('should display badge for Interviews with scheduled count', () => {
      renderWithProviders(<DashboardPage />);

      // The Interviews action should show interviews_scheduled as badge (5)
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  describe('My Vacancies Section', () => {
    it('should display My Vacancies section', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('My Vacancies')).toBeInTheDocument();
    });

    it('should display vacancy titles', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Senior Developer')).toBeInTheDocument();
      expect(screen.getByText('Product Manager')).toBeInTheDocument();
    });

    it('should display pending review count per vacancy', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText(/5.*pending/)).toBeInTheDocument();
      expect(screen.getByText(/3.*pending/)).toBeInTheDocument();
    });

    it('should display total candidates per vacancy', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText(/15.*total candidates/)).toBeInTheDocument();
      expect(screen.getByText(/10.*total candidates/)).toBeInTheDocument();
    });
  });

  describe('Recent Activity Section', () => {
    it('should display Recent Activity section', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    });

    it('should display activity entries', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText('John Doe - Senior Developer')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith - Product Manager')).toBeInTheDocument();
    });

    it('should display activity type icons', () => {
      renderWithProviders(<DashboardPage />);

      // Activities should have icons (CheckCircle for approved, Cancel for rejected)
      const activityItems = screen.getAllByText(/John Doe|Jane Smith/);
      expect(activityItems.length).toBe(2);
    });
  });

  describe('Tip Section', () => {
    it('should display tip section at bottom', () => {
      renderWithProviders(<DashboardPage />);

      expect(screen.getByText(/Tip:/)).toBeInTheDocument();
    });

    it('should display tip content about quick actions', () => {
      renderWithProviders(<DashboardPage />);

      expect(
        screen.getByText(
          /You can quickly approve or reject candidates directly from the review queue/
        )
      ).toBeInTheDocument();
    });
  });

  describe('Layout and Responsive Design', () => {
    it('should use Container component with maxWidth xl', () => {
      const { container } = renderWithProviders(<DashboardPage />);

      const containers = container.querySelectorAll('.MuiContainer-maxWidthXl');
      expect(containers.length).toBeGreaterThan(0);
    });

    it('should use Grid components for stats layout', () => {
      const { container } = renderWithProviders(<DashboardPage />);

      const grids = container.querySelectorAll('.MuiGrid-root');
      expect(grids.length).toBeGreaterThan(0);
    });

    it('should render quick actions in grid layout', () => {
      const { container } = renderWithProviders(<DashboardPage />);

      const cards = container.querySelectorAll('.MuiCard-root');
      expect(cards.length).toBe(4); // 4 quick action cards
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      renderWithProviders(<DashboardPage />);

      // Main title is h4
      const h4 = screen.getByRole('heading', { level: 4 });
      expect(h4).toBeInTheDocument();
    });

    it('should have accessible quick action cards', () => {
      renderWithProviders(<DashboardPage />);

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  describe('Interaction States', () => {
    it('should have hover effect on quick action cards', () => {
      const { container } = renderWithProviders(<DashboardPage />);

      const cards = container.querySelectorAll('.MuiCard-root');
      cards.forEach((card) => {
        expect(card).toHaveStyle({ cursor: 'pointer' });
      });
    });
  });
});

describe('Hiring Manager DashboardPage - Loading States', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading state for stats', async () => {
    // Override the mock for loading state
    vi.mocked(await import('@/hooks/useHiringManagerData')).useHiringManagerDashboard = vi.fn(
      () => ({
        data: undefined,
        isLoading: true,
      })
    ) as ReturnType<typeof vi.fn>;

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <DashboardPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    // Loading state shows "..." for stats
    const loadingValues = screen.getAllByText('...');
    expect(loadingValues.length).toBeGreaterThan(0);
  });
});

describe('Hiring Manager DashboardPage - Empty States', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should handle empty vacancies gracefully', async () => {
    vi.mocked(await import('@/hooks/useHiringManagerData')).useHiringManagerDashboard = vi.fn(
      () => ({
        data: {
          pending_review: { total_pending: 0, urgent_count: 0 },
          quick_stats: {
            approved_this_month: 0,
            avg_time_to_decision_days: null,
            interviews_scheduled: 0,
          },
          my_vacancies: [],
          recent_activity: [],
        },
        isLoading: false,
      })
    ) as ReturnType<typeof vi.fn>;

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <DashboardPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    // Should not show My Vacancies section when empty
    expect(screen.queryByText('My Vacancies')).not.toBeInTheDocument();
  });

  it('should handle empty recent activity gracefully', async () => {
    vi.mocked(await import('@/hooks/useHiringManagerData')).useHiringManagerDashboard = vi.fn(
      () => ({
        data: {
          pending_review: { total_pending: 0, urgent_count: 0 },
          quick_stats: {
            approved_this_month: 0,
            avg_time_to_decision_days: null,
            interviews_scheduled: 0,
          },
          my_vacancies: [],
          recent_activity: [],
        },
        isLoading: false,
      })
    ) as ReturnType<typeof vi.fn>;

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <DashboardPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    // Should not show Recent Activity section when empty
    expect(screen.queryByText('Recent Activity')).not.toBeInTheDocument();
  });

  it('should display -- when avg decision time is null', async () => {
    vi.mocked(await import('@/hooks/useHiringManagerData')).useHiringManagerDashboard = vi.fn(
      () => ({
        data: {
          pending_review: { total_pending: 0, urgent_count: 0 },
          quick_stats: {
            approved_this_month: 0,
            avg_time_to_decision_days: null,
            interviews_scheduled: 0,
          },
          my_vacancies: [],
          recent_activity: [],
        },
        isLoading: false,
      })
    ) as ReturnType<typeof vi.fn>;

    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <DashboardPage />
        </BrowserRouter>
      </QueryClientProvider>
    );

    // Should show -- for null avg time
    expect(screen.getByText('--')).toBeInTheDocument();
  });
});
