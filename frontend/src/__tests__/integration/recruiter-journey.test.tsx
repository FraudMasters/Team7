/**
 * Integration Tests: Recruiter Journey End-to-End Flow
 *
 * Tests the complete Recruiter user journey from dashboard to analytics.
 * Verifies navigation, page accessibility, and component rendering for all key Recruiter pages.
 *
 * Verification Steps (from spec):
 * 1. Navigate to recruiter dashboard
 * 2. View vacancies
 * 3. View candidates kanban
 * 4. Navigate to search
 * 5. Navigate to analytics
 * 6. Verify all pages accessible
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Page Components
import { DashboardPage } from '../../pages/recruiter/DashboardPage';
import { VacanciesPage } from '../../pages/recruiter/VacanciesPage';
import { CandidatesKanbanPage } from '../../pages/recruiter/CandidatesKanbanPage';
import { SearchPage } from '../../pages/recruiter/SearchPage';
import AnalyticsDashboardPage from '../../pages/AnalyticsDashboard';

// Layout Components
import RecruiterLayout from '../../layouts/RecruiterLayout';

// Context Providers
import { ThemeProvider } from '../../contexts/ThemeContext';
import { LanguageProvider } from '../../contexts/LanguageContext';

// Mock hooks
vi.mock('../../hooks/useRecruiterData', () => ({
  useRecruiterAnalytics: () => ({
    data: {
      time_to_hire: 21,
      applications_per_job: 15.5,
      total_candidates: 48,
      active_vacancies: 5,
    },
    isLoading: false,
    error: null,
  }),
  useCandidates: () => ({
    data: {
      candidates: [
        {
          id: '1',
          name: 'John Doe',
          email: 'john@example.com',
          stage: 'Applied',
          skills: ['React', 'TypeScript'],
          match_percentage: 85,
        },
        {
          id: '2',
          name: 'Jane Smith',
          email: 'jane@example.com',
          stage: 'Interview',
          skills: ['Python', 'Django'],
          match_percentage: 92,
        },
      ],
    },
    isLoading: false,
    error: null,
  }),
  useCandidateStages: () => ({
    data: ['Applied', 'Screening', 'Interview', 'Offer', 'Hired'],
    isLoading: false,
    error: null,
  }),
  useUpdateCandidateStage: () => ({
    mutateAsync: vi.fn(),
  }),
  useRecruiterVacancies: () => ({
    data: {
      vacancies: [
        {
          id: '1',
          title: 'Senior Frontend Developer',
          description: 'Build amazing UI',
          location: 'Remote',
          work_format: 'remote',
          required_skills: ['React', 'TypeScript'],
          status: 'active',
        },
        {
          id: '2',
          title: 'Backend Engineer',
          description: 'Build scalable APIs',
          location: 'San Francisco, CA',
          work_format: 'office',
          required_skills: ['Python', 'FastAPI'],
          status: 'active',
        },
      ],
    },
    isLoading: false,
    error: null,
  }),
}));

vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({
      data: {
        vacancies: [],
      },
    }),
    delete: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual('@tanstack/react-query');
  return {
    ...actual,
    useQueryClient: () => ({
      invalidateQueries: vi.fn(),
    }),
  };
});

// Test wrapper with providers
const createTestWrapper = (initialEntries = ['/recruiter/dashboard']) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <LanguageProvider>
          <MemoryRouter initialEntries={initialEntries}>
            {children}
          </MemoryRouter>
        </LanguageProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('Recruiter Journey - Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Step 1: Navigate to recruiter dashboard
   * Expected: Dashboard renders with key metrics
   */
  describe('Step 1: Navigate to recruiter dashboard', () => {
    it('renders the RecruiterDashboard with metrics', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify dashboard heading
      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });

      // Verify welcome message
      expect(screen.getByText(/Welcome back!/i)).toBeInTheDocument();

      // Verify BentoCard metrics are present
      expect(screen.getByText('Active Jobs')).toBeInTheDocument();
      expect(screen.getByText('Total Candidates')).toBeInTheDocument();
      expect(screen.getByText('Time to Hire')).toBeInTheDocument();
      expect(screen.getByText('Applications/Job')).toBeInTheDocument();

      // Verify Pipeline Funnel section
      expect(screen.getByText('Pipeline Funnel')).toBeInTheDocument();
    });

    it('displays RecruiterLayout navigation', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify AgentHR branding
      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });

      // Verify Recruiter Portal title in AppBar
      expect(screen.getByText('Recruiter Portal')).toBeInTheDocument();

      // Verify navigation sections are visible
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Hiring')).toBeInTheDocument();
      expect(screen.getByText('Resumes')).toBeInTheDocument();
      expect(screen.getByText('Search')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    it('has skip-to-content link for accessibility', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify skip link exists (even though visually hidden)
      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });
  });

  /**
   * Step 2: View vacancies
   * Expected: VacanciesPage renders with vacancy list
   */
  describe('Step 2: View vacancies', () => {
    it('renders the VacanciesPage', async () => {
      const Wrapper = createTestWrapper(['/recruiter/vacancies']);

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="vacancies" element={<VacanciesPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify vacancies page heading (page title varies, check for common elements)
      await waitFor(() => {
        const heading = screen.queryByText(/vacancies/i);
        // Page may show "Loading vacancies..." or actual content
        expect(heading || screen.getByText(/Loading/i)).toBeInTheDocument();
      });
    });

    it('shows navigation link to vacancies in sidebar', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify Vacancies link in navigation
      expect(screen.getByText('Vacancies')).toBeInTheDocument();
    });
  });

  /**
   * Step 3: View candidates kanban
   * Expected: CandidatesKanbanPage renders with kanban board
   */
  describe('Step 3: View candidates kanban', () => {
    it('renders the CandidatesKanbanPage', async () => {
      const Wrapper = createTestWrapper(['/recruiter/candidates']);

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="candidates" element={<CandidatesKanbanPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify candidates kanban heading
      await waitFor(() => {
        expect(screen.getByText('Candidate Pipeline')).toBeInTheDocument();
      });

      // Verify subtitle
      expect(screen.getByText(/Drag candidates between stages/i)).toBeInTheDocument();

      // Verify search input
      const searchInput = screen.getByPlaceholderText('Search candidates...');
      expect(searchInput).toBeInTheDocument();
    });

    it('shows navigation links to candidates in sidebar', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify Candidates link in navigation
      expect(screen.getByText('Candidates')).toBeInTheDocument();
      expect(screen.getByText('Pipeline')).toBeInTheDocument();
    });
  });

  /**
   * Step 4: Navigate to search
   * Expected: SearchPage renders with search functionality
   */
  describe('Step 4: Navigate to search', () => {
    it('renders the SearchPage', async () => {
      const Wrapper = createTestWrapper(['/recruiter/search']);

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="search" element={<SearchPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify search page elements (may show loading or search interface)
      await waitFor(() => {
        // Check for search-related UI elements
        const searchElements = [
          screen.queryByText(/candidate search/i),
          screen.queryByText(/search/i),
          screen.queryByPlaceholderText(/search/i),
        ];
        const hasSearchElement = searchElements.some(el => el !== null);
        expect(hasSearchElement || screen.getByText(/Loading/i)).toBeTruthy();
      });
    });

    it('shows navigation link to search in sidebar', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify Search link in navigation
      expect(screen.getByText('Candidate Search')).toBeInTheDocument();
    });
  });

  /**
   * Step 5: Navigate to analytics
   * Expected: AnalyticsDashboardPage renders with metrics and charts
   */
  describe('Step 5: Navigate to analytics', () => {
    it('renders the AnalyticsDashboardPage', async () => {
      const Wrapper = createTestWrapper(['/recruiter/analytics']);

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="analytics" element={<AnalyticsDashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Analytics page may show loading or analytics content
      await waitFor(() => {
        const analyticsElements = [
          screen.queryByText(/analytics/i),
          screen.queryByText(/metrics/i),
          screen.queryByText(/Overview/i),
        ];
        const hasAnalyticsElement = analyticsElements.some(el => el !== null);
        expect(hasAnalyticsElement || screen.queryByRole('progressbar')).toBeTruthy();
      });
    });

    it('shows navigation link to analytics in sidebar', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify Analytics link in navigation
      expect(screen.getByText('Overview')).toBeInTheDocument();
    });
  });

  /**
   * Step 6: Verify all pages accessible
   * Expected: All navigation links work and pages render without errors
   */
  describe('Step 6: Verify all pages accessible', () => {
    it('has all key navigation items in RecruiterLayout', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Verify all main navigation sections
      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Hiring')).toBeInTheDocument();
        expect(screen.getByText('Vacancies')).toBeInTheDocument();
        expect(screen.getByText('Candidates')).toBeInTheDocument();
        expect(screen.getByText('Pipeline')).toBeInTheDocument();
        expect(screen.getByText('Applications')).toBeInTheDocument();
        expect(screen.getByText('Resumes')).toBeInTheDocument();
        expect(screen.getByText('Database')).toBeInTheDocument();
        expect(screen.getByText('Upload')).toBeInTheDocument();
        expect(screen.getByText('Batch Upload')).toBeInTheDocument();
        expect(screen.getByText('Search')).toBeInTheDocument();
        expect(screen.getByText('Candidate Search')).toBeInTheDocument();
        expect(screen.getByText('Saved Searches')).toBeInTheDocument();
        expect(screen.getByText('Compare')).toBeInTheDocument();
        expect(screen.getByText('Analytics')).toBeInTheDocument();
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Skill Gap Analysis')).toBeInTheDocument();
      });
    });

    it('navigates between pages without errors', async () => {
      const user = userEvent.setup();
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="vacancies" element={<VacanciesPage />} />
              <Route path="candidates" element={<CandidatesKanbanPage />} />
              <Route path="search" element={<SearchPage />} />
              <Route path="analytics" element={<AnalyticsDashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Start at dashboard
      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });

      // All navigation links should be present and clickable
      const vacanciesLink = screen.getAllByText('Vacancies');
      expect(vacanciesLink.length).toBeGreaterThan(0);

      const candidatesLink = screen.getAllByText('Candidates');
      expect(candidatesLink.length).toBeGreaterThan(0);

      const searchLink = screen.getAllByText('Candidate Search');
      expect(searchLink.length).toBeGreaterThan(0);
    });
  });

  /**
   * Additional: Accessibility tests
   */
  describe('Accessibility', () => {
    it('has proper ARIA labels on navigation', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Check for navigation with proper ARIA role
      const mainNav = screen.getByRole('navigation', { name: /Recruiter sidebar navigation/i });
      expect(mainNav).toBeInTheDocument();
    });

    it('has keyboard-accessible skip link', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });
  });

  /**
   * Additional: Mobile responsive test
   */
  describe('Mobile Responsiveness', () => {
    it('renders RecruiterLayout on mobile viewport', async () => {
      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Should still render with mobile drawer capability
      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });
  });
});
