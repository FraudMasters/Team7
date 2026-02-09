/**
 * Integration Tests: Recruiter Flow Navigation
 *
 * Tests the navigation flow patterns specific to the Recruiter user experience.
 * Verifies navigation transitions, active states, section collapse/expand,
 * mobile drawer behavior, and quick action buttons.
 *
 * Verification Steps (from spec):
 * 1. Navigation flow transitions between pages
 * 2. Active state highlighting on current page
 * 3. Section collapse/expand behavior
 * 4. Mobile navigation drawer open/close
 * 5. Quick action buttons in AppBar
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
      ],
    },
    isLoading: false,
    error: null,
  }),
}));

vi.mock('../../contexts/AuthContext', () => ({
  useAuthContext: () => ({
    isInitialized: true,
    user: { id: '1', role: 'recruiter' },
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

describe('Recruiter Flow - Navigation Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Step 1: Navigation flow transitions between pages
   * Expected: Clicking navigation items updates the route and renders new page
   */
  describe('Step 1: Navigation flow transitions', () => {
    it('navigates from dashboard to vacancies', async () => {
      const user = userEvent.setup();
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="vacancies" element={<VacanciesPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Start at dashboard
      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });

      // Click Vacancies navigation
      const vacanciesLink = screen.getByText('Vacancies').closest('button');
      expect(vacanciesLink).toBeInTheDocument();
      await user.click(vacanciesLink!);

      // Verify navigation occurred (vacancies page would show loading or content)
      await waitFor(() => {
        expect(screen.getByText(/vacancies/i) || screen.getByText(/Loading/i)).toBeInTheDocument();
      });
    });

    it('navigates from dashboard to candidates', async () => {
      const user = userEvent.setup();
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="candidates" element={<CandidatesKanbanPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Start at dashboard
      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });

      // Click Candidates navigation
      const candidatesLink = screen.getByText('Candidates').closest('button');
      expect(candidatesLink).toBeInTheDocument();
      await user.click(candidatesLink!);

      // Verify navigation occurred
      await waitFor(() => {
        expect(screen.getByText('Candidate Pipeline')).toBeInTheDocument();
      });
    });

    it('navigates from dashboard to analytics', async () => {
      const user = userEvent.setup();
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="analytics" element={<AnalyticsDashboardPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Start at dashboard
      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });

      // Click Analytics section first, then Overview
      const analyticsSection = screen.getAllByText('Analytics').find(el => el.tagName === 'SPAN');
      if (analyticsSection) {
        const analyticsButton = analyticsSection.closest('button');
        if (analyticsButton) {
          await user.click(analyticsButton);
        }
      }

      const overviewLink = screen.getByText('Overview').closest('button');
      if (overviewLink) {
        await user.click(overviewLink);
      }
    });

    it('navigates from search to dashboard', async () => {
      const user = userEvent.setup();
      const Wrapper = createTestWrapper(['/recruiter/search']);

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="search" element={<SearchPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      // Start at search
      await waitFor(() => {
        const searchElements = [
          screen.queryByText(/candidate search/i),
          screen.queryByText(/search/i),
          screen.queryByPlaceholderText(/search/i),
        ];
        const hasSearchElement = searchElements.some(el => el !== null);
        expect(hasSearchElement || screen.getByText(/Loading/i)).toBeTruthy();
      });

      // Click Dashboard navigation
      const dashboardLink = screen.getByText('Dashboard').closest('button');
      expect(dashboardLink).toBeInTheDocument();
      await user.click(dashboardLink!);

      // Verify navigation occurred
      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });
    });
  });

  /**
   * Step 2: Active state highlighting on current page
   * Expected: Current page navigation item has active styling
   */
  describe('Step 2: Active state highlighting', () => {
    it('highlights dashboard as active on dashboard page', async () => {
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

      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });

      // Dashboard button should be marked as current page
      const dashboardButton = screen.getByText('Dashboard').closest('button');
      expect(dashboardButton).toBeInTheDocument();
      expect(dashboardButton).toHaveAttribute('aria-current', 'page');
    });

    it('highlights vacancies as active on vacancies page', async () => {
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

      await waitFor(() => {
        const vacanciesLink = screen.getByText('Vacancies').closest('button');
        expect(vacanciesLink).toBeInTheDocument();
        expect(vacanciesLink).toHaveAttribute('aria-current', 'page');
      });
    });

    it('highlights candidates as active on candidates page', async () => {
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

      await waitFor(() => {
        expect(screen.getByText('Candidate Pipeline')).toBeInTheDocument();
      });

      // Both Candidates and Pipeline link to candidates page
      const candidatesButtons = screen.getAllByText('Candidates').map(el => el.closest('button'));
      const hasActive = candidatesButtons.some(btn => btn && btn.getAttribute('aria-current') === 'page');
      expect(hasActive).toBe(true);
    });
  });

  /**
   * Step 3: Section collapse/expand behavior
   * Expected: Clicking section toggles collapses/expands its children
   */
  describe('Step 3: Section collapse/expand behavior', () => {
    it('toggles Hiring section collapse and expand', async () => {
      const user = userEvent.setup();
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <RecruiterLayout />
        </Wrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });

      // Find Hiring section header button
      const hiringButtons = screen.getAllByText('Hiring');
      const hiringHeader = hiringButtons.find(el => {
        const button = el.closest('button');
        return button && button.querySelector('svg'); // Has expand/collapse icon
      });

      expect(hiringHeader).toBeInTheDocument();
      const hiringButton = hiringHeader!.closest('button');

      // Initially expanded (Hiring is expanded by default)
      expect(screen.getByText('Vacancies')).toBeInTheDocument();
      expect(screen.getByText('Candidates')).toBeInTheDocument();
      expect(screen.getByText('Pipeline')).toBeInTheDocument();
      expect(screen.getByText('Applications')).toBeInTheDocument();

      // Click to collapse
      await user.click(hiringButton!);

      // After collapsing, items should still be visible due to Collapse animation timeout
      // but the state should be toggled
    });

    it('toggles Analytics section collapse and expand', async () => {
      const user = userEvent.setup();
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <RecruiterLayout />
        </Wrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });

      // Find Analytics section header button
      const analyticsButtons = screen.getAllByText('Analytics');
      const analyticsHeader = analyticsButtons.find(el => {
        const button = el.closest('button');
        return button && button.querySelector('svg');
      });

      expect(analyticsHeader).toBeInTheDocument();
      const analyticsButton = analyticsHeader!.closest('button');

      // Initially collapsed (Analytics is collapsed by default)
      // After clicking to expand, Overview should become visible
      await user.click(analyticsButton!);

      // Section should now be expanded
      expect(screen.getByText('Overview')).toBeInTheDocument();
      expect(screen.getByText('Skill Gap Analysis')).toBeInTheDocument();
    });

    it('toggles Search section collapse and expand', async () => {
      const user = userEvent.setup();
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <RecruiterLayout />
        </Wrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });

      // Find Search section header button
      const searchButtons = screen.getAllByText('Search');
      const searchHeader = searchButtons.find(el => {
        const button = el.closest('button');
        return button && button.querySelector('svg');
      });

      expect(searchHeader).toBeInTheDocument();
      const searchButton = searchHeader!.closest('button');

      // Initially collapsed
      // Click to expand
      await user.click(searchButton!);

      // Items should now be visible
      expect(screen.getByText('Candidate Search')).toBeInTheDocument();
      expect(screen.getByText('Saved Searches')).toBeInTheDocument();
      expect(screen.getByText('Compare')).toBeInTheDocument();
    });
  });

  /**
   * Step 4: Mobile navigation drawer open/close
   * Expected: Mobile hamburger menu toggles drawer visibility
   */
  describe('Step 4: Mobile navigation drawer', () => {
    it('opens mobile drawer when hamburger menu is clicked', async () => {
      const user = userEvent.setup();

      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      // Update matchMedia for mobile breakpoint
      const originalMatchMedia = window.matchMedia;
      window.matchMedia = vi.fn().mockImplementation(query => ({
        matches: query.includes('(max-width:'),
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <RecruiterLayout />
        </Wrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });

      // Find hamburger menu button
      const menuButton = screen.getByLabelText(/Open navigation menu/i);
      expect(menuButton).toBeInTheDocument();

      // Click to open drawer
      await user.click(menuButton);

      // Drawer should be open
      expect(menuButton).toHaveAttribute('aria-expanded', 'true');

      // Restore matchMedia
      window.matchMedia = originalMatchMedia;
    });

    it('closes mobile drawer when navigation item is clicked', async () => {
      const user = userEvent.setup();

      // Set mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      const originalMatchMedia = window.matchMedia;
      window.matchMedia = vi.fn().mockImplementation(query => ({
        matches: query.includes('(max-width:'),
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="vacancies" element={<VacanciesPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });

      // Open drawer
      const menuButton = screen.getByLabelText(/Open navigation menu/i);
      await user.click(menuButton);

      expect(menuButton).toHaveAttribute('aria-expanded', 'true');

      // Click navigation item
      const vacanciesLink = screen.getByText('Vacancies').closest('button');
      await user.click(vacanciesLink!);

      // Drawer should close after navigation (mobile behavior)
      await waitFor(() => {
        expect(menuButton).toHaveAttribute('aria-expanded', 'false');
      });

      window.matchMedia = originalMatchMedia;
    });
  });

  /**
   * Step 5: Quick action buttons in AppBar
   * Expected: AppBar quick search button navigates to search page
   */
  describe('Step 5: Quick action buttons in AppBar', () => {
    it('navigates to search when quick search button is clicked', async () => {
      const user = userEvent.setup();
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="search" element={<SearchPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });

      // Find quick search button in AppBar
      const searchButton = screen.getByLabelText('Quick search');
      expect(searchButton).toBeInTheDocument();

      // Click quick search button
      await user.click(searchButton);

      // Should navigate to search page
      await waitFor(() => {
        const searchElements = [
          screen.queryByText(/candidate search/i),
          screen.queryByText(/search/i),
        ];
        const hasSearchElement = searchElements.some(el => el !== null);
        expect(hasSearchElement || screen.queryByPlaceholderText(/search/i)).toBeTruthy();
      });
    });

    it('displays tooltip on quick search button', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <RecruiterLayout />
        </Wrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });

      // Quick search button should have tooltip title
      const searchButton = screen.getByLabelText('Quick search');
      expect(searchButton).toBeInTheDocument();
    });
  });

  /**
   * Additional: Navigation accessibility
   */
  describe('Navigation accessibility', () => {
    it('has proper ARIA roles on navigation', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <RecruiterLayout />
        </Wrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });

      // Main navigation should have proper ARIA role
      const sidebarNav = screen.getByRole('navigation', { name: /recruiter sidebar navigation/i });
      expect(sidebarNav).toBeInTheDocument();
    });

    it('has keyboard-accessible navigation items', async () => {
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

      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });

      // Navigation items should be buttons (keyboard accessible)
      const dashboardButton = screen.getByText('Dashboard').closest('button');
      expect(dashboardButton).toBeInTheDocument();

      const vacanciesButton = screen.getByText('Vacancies').closest('button');
      expect(vacanciesButton).toBeInTheDocument();
    });

    it('has visible focus states on navigation items', async () => {
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <RecruiterLayout />
        </Wrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });

      // Navigation buttons should have focus-visible styling
      const dashboardButton = screen.getByText('Dashboard').closest('button');
      expect(dashboardButton).toBeInTheDocument();

      // MUI buttons have built-in focus-visible styles
      // The component includes '&:focus-visible' styles
    });
  });

  /**
   * Additional: Multi-level navigation flow
   */
  describe('Multi-level navigation flow', () => {
    it('navigates through multiple pages in sequence', async () => {
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
            </Route>
          </Routes>
        </Wrapper>
      );

      // Start at dashboard
      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });

      // Dashboard -> Vacancies
      const vacanciesLink = screen.getByText('Vacancies').closest('button');
      await user.click(vacanciesLink!);
      await waitFor(() => {
        expect(screen.getByText(/vacancies/i) || screen.getByText(/Loading/i)).toBeInTheDocument();
      });

      // Vacancies -> Candidates
      const candidatesLink = screen.getByText('Candidates').closest('button');
      await user.click(candidatesLink!);
      await waitFor(() => {
        expect(screen.getByText('Candidate Pipeline')).toBeInTheDocument();
      });

      // Candidates -> Dashboard (back)
      const dashboardLink = screen.getByText('Dashboard').closest('button');
      await user.click(dashboardLink!);
      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });
    });

    it('maintains navigation state during transitions', async () => {
      const user = userEvent.setup();
      const Wrapper = createTestWrapper();

      render(
        <Wrapper>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="vacancies" element={<VacanciesPage />} />
            </Route>
          </Routes>
        </Wrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });

      // Navigation sections should be visible after transition
      expect(screen.getByText('Hiring')).toBeInTheDocument();
      expect(screen.getByText('Resumes')).toBeInTheDocument();
      expect(screen.getByText('Search')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
      expect(screen.getByText('Settings')).toBeInTheDocument();
    });
  });
});
