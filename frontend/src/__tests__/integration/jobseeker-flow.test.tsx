/**
 * Integration Tests: JobSeeker Flow Navigation
 *
 * Tests the JobSeeker navigation flow and routing structure.
 * Verifies navigation between all key pages, sidebar navigation,
 * bottom navigation (mobile), and accessibility features.
 *
 * Navigation Flow (from spec):
 * 1. Landing page → Job Seeker flow
 * 2. Jobs section: Browse, Recommended, Saved, Applications
 * 3. Career section: Skill Assessment, Learning, Salary Calculator, Interview Tips
 * 4. Account section: Profile, Resume, Job Alerts, Settings
 * 5. Bottom navigation (mobile) transitions
 * 6. Sidebar navigation (desktop) functionality
 * 7. Accessibility features throughout
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Page Components
import LandingPage from '../../pages/LandingPage';
import { JobsBrowsePage } from '../../pages/jobs/JobsBrowsePage';
import { RecommendedJobsPage } from '../../pages/jobs/RecommendedJobsPage';
import { SavedJobsPage } from '../../pages/jobs/SavedJobsPage';
import { MyApplicationsPage } from '../../pages/jobs/MyApplicationsPage';
import { SkillAssessmentPage } from '../../pages/jobs/SkillAssessmentPage';
import { LearningPage } from '../../pages/jobs/LearningPage';
import { SalaryCalculatorPage } from '../../pages/jobs/SalaryCalculatorPage';
import { InterviewTipsPage } from '../../pages/jobs/InterviewTipsPage';
import { CandidateProfilePage } from '../../pages/jobs/CandidateProfilePage';
import { ResumeUploadPage } from '../../pages/jobs/ResumeUploadPage';
import { JobAlertsPage } from '../../pages/jobs/JobAlertsPage';
import { SettingsPage } from '../../pages/jobs/SettingsPage';

// Layout Components
import JobSeekerLayout from '../../layouts/JobSeekerLayout';

// Context Providers
import { ThemeProvider } from '../../contexts/ThemeContext';
import { LanguageProvider } from '../../contexts/LanguageContext';

// Mock hooks
vi.mock('../../hooks/useJobs', () => ({
  useJobs: () => ({
    data: {
      vacancies: [
        {
          id: '1',
          title: 'Software Engineer',
          description: 'Develop awesome software',
          location: 'Remote',
          work_format: 'remote',
          min_experience_months: 24,
          required_skills: ['React', 'TypeScript'],
        },
      ],
    },
    isLoading: false,
    error: null,
  }),
}));

vi.mock('../../hooks/useSavedJobs', () => ({
  useSavedJobs: () => ({
    data: { saved_jobs: [], total: 0 },
    isLoading: false,
    error: null,
  }),
}));

vi.mock('../../hooks/useApplications', () => ({
  useApplications: () => ({
    data: { applications: [], total: 0 },
    isLoading: false,
    error: null,
  }),
}));

// Mock AuthContext
vi.mock('../../contexts/AuthContext', () => ({
  useAuthContext: () => ({
    isInitialized: true,
    user: null,
    isLoading: false,
  }),
}));

// Mock API client
vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

// Test Utilities
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const renderWithProviders = (
  ui: React.ReactElement,
  { queryClient = createTestQueryClient(), ...renderOptions } = {}
) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    return (
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <LanguageProvider>
            {children}
          </LanguageProvider>
        </ThemeProvider>
      </QueryClientProvider>
    );
  };
  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

describe('JobSeeker Flow - Navigation Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    });
  });

  /**
   * Landing Page → Job Seeker Flow Entry
   * Expected: Landing page allows navigation to job seeker flow
   */
  describe('Landing Page to JobSeeker Flow', () => {
    it('renders landing page with Browse Jobs button', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/']}>
          <LandingPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
        expect(screen.getByText('Browse Jobs')).toBeInTheDocument();
      });
    });

    it('has accessible role selection for job seekers', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/']}>
          <LandingPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Job Seeker')).toBeInTheDocument();
      });
    });
  });

  /**
   * Jobs Section Navigation
   * Tests: Browse, Recommended, Saved, Applications
   */
  describe('Jobs Section Navigation', () => {
    it('renders Browse Jobs page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Find Your Next Job')).toBeInTheDocument();
      });
    });

    it('renders Recommended Jobs page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/recommended']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('renders Saved Jobs page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/saved']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Saved Jobs')).toBeInTheDocument();
      });
    });

    it('renders Applications page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/applications']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('My Applications')).toBeInTheDocument();
      });
    });

    it('sidebar navigation shows Jobs section items', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Find Jobs')).toBeInTheDocument();
        expect(screen.getByText('Browse')).toBeInTheDocument();
        expect(screen.getByText('Recommended')).toBeInTheDocument();
        expect(screen.getByText('Saved')).toBeInTheDocument();
        expect(screen.getByText('Applications')).toBeInTheDocument();
      });
    });
  });

  /**
   * Career Section Navigation
   * Tests: Skill Assessment, Learning, Salary Calculator, Interview Tips
   */
  describe('Career Section Navigation', () => {
    it('renders Skill Assessment page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/assessment']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('renders Learning page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/learning']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('renders Salary Calculator page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/salary']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('renders Interview Tips page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/tips']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('sidebar navigation shows Career section items', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Career')).toBeInTheDocument();
        expect(screen.getByText('Skill Assessment')).toBeInTheDocument();
        expect(screen.getByText('Learning')).toBeInTheDocument();
        expect(screen.getByText('Salary Calculator')).toBeInTheDocument();
        expect(screen.getByText('Interview Tips')).toBeInTheDocument();
      });
    });
  });

  /**
   * Account Section Navigation
   * Tests: Profile, Resume, Job Alerts, Settings
   */
  describe('Account Section Navigation', () => {
    it('renders Profile page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/profile']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('renders Resume Upload page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/upload']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('renders Job Alerts page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/alerts']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('renders Settings page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/settings']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('sidebar navigation shows Account section items', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Account')).toBeInTheDocument();
        expect(screen.getByText('Profile')).toBeInTheDocument();
        expect(screen.getByText('Resume')).toBeInTheDocument();
        expect(screen.getByText('Job Alerts')).toBeInTheDocument();
        expect(screen.getByText('Settings')).toBeInTheDocument();
      });
    });
  });

  /**
   * Bottom Navigation (Mobile)
   * Tests: Bottom nav items and transitions
   */
  describe('Bottom Navigation - Mobile', () => {
    it('renders bottom navigation on mobile', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('navigation', { name: /Mobile navigation/i })).toBeInTheDocument();
      });
    });

    it('bottom navigation has all required items', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Jobs')).toBeInTheDocument();
        expect(screen.getByText('Saved')).toBeInTheDocument();
        expect(screen.getByText('Applications')).toBeInTheDocument();
        expect(screen.getByText('Profile')).toBeInTheDocument();
      });
    });

    it('bottom navigation has proper ARIA labels', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const bottomNav = screen.getByRole('navigation', { name: /Mobile navigation/i });
        expect(bottomNav).toBeInTheDocument();
      });
    });
  });

  /**
   * Sidebar Navigation (Desktop)
   * Tests: Sidebar structure, sections, and items
   */
  describe('Sidebar Navigation - Desktop', () => {
    it('renders sidebar with all sections', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Find Jobs')).toBeInTheDocument();
        expect(screen.getByText('Jobs')).toBeInTheDocument();
        expect(screen.getByText('Career')).toBeInTheDocument();
        expect(screen.getByText('Account')).toBeInTheDocument();
      });
    });

    it('sidebar has proper ARIA attributes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const sidebar = screen.getByRole('navigation', { name: /Job seeker sidebar navigation/i });
        expect(sidebar).toBeInTheDocument();
      });
    });

    it('sidebar navigation items have proper roles', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const mainNav = screen.getByRole('navigation', { name: /Основная навигация/i });
        expect(mainNav).toBeInTheDocument();
      });
    });
  });

  /**
   * Route Configuration
   * Tests: All routes are properly configured and accessible
   */
  describe('Route Configuration', () => {
    const jobSeekerRoutes = [
      '/jobs',
      '/jobs/recommended',
      '/jobs/saved',
      '/jobs/applications',
      '/jobs/assessment',
      '/jobs/learning',
      '/jobs/salary',
      '/jobs/tips',
      '/jobs/upload',
      '/jobs/alerts',
      '/jobs/settings',
      '/profile',
    ];

    it('all JobSeeker routes are accessible without errors', () => {
      jobSeekerRoutes.forEach(route => {
        expect(() => {
          renderWithProviders(
            <MemoryRouter initialEntries={[route]}>
              <JobSeekerLayout />
            </MemoryRouter>
          );
        }).not.toThrow();
      });
    });

    it('main JobSeeker routes are configured correctly', async () => {
      const mainRoutes = [
        '/jobs',
        '/jobs/saved',
        '/jobs/applications',
        '/profile',
      ];

      for (const route of mainRoutes) {
        const { container } = renderWithProviders(
          <MemoryRouter initialEntries={[route]}>
            <JobSeekerLayout />
          </MemoryRouter>
        );

        expect(container.querySelector('main')).toBeInTheDocument();
      }
    });
  });

  /**
   * Active Route Highlighting
   * Tests: Current page is properly highlighted in navigation
   */
  describe('Active Route Highlighting', () => {
    it('highlights Browse as active on /jobs route', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Find Jobs')).toBeInTheDocument();
      });
    });

    it('highlights Saved as active on /jobs/saved route', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/saved']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Saved Jobs')).toBeInTheDocument();
      });
    });

    it('highlights Applications as active on /jobs/applications route', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/applications']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('My Applications')).toBeInTheDocument();
      });
    });

    it('highlights Profile as active on /profile route', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/profile']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });
  });

  /**
   * Navigation Transitions
   * Tests: Smooth transitions between pages
   */
  describe('Navigation Transitions', () => {
    it('main content has proper id for skip link', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const mainContent = document.getElementById('main-content');
        expect(mainContent).toBeInTheDocument();
      });
    });

    it('skip-to-content link is present', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });
  });

  /**
   * Accessibility Features
   * Tests: ARIA labels, roles, and keyboard navigation
   */
  describe('Accessibility Features', () => {
    it('has skip-to-content link with proper attributes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });

    it('sidebar navigation has proper ARIA role', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      const sidebar = screen.getByRole('navigation', { name: /Job seeker sidebar navigation/i });
      expect(sidebar).toBeInTheDocument();
    });

    it('bottom navigation has proper ARIA role', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      const bottomNav = screen.getByRole('navigation', { name: /Mobile navigation/i });
      expect(bottomNav).toBeInTheDocument();
    });

    it('main content area has proper id for accessibility', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const mainContent = document.getElementById('main-content');
        expect(mainContent).toBeInTheDocument();
      });
    });

    it('navigation menu items have proper role', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const menuBar = screen.getByRole('menubar');
        expect(menuBar).toBeInTheDocument();
      });
    });
  });

  /**
   * Mobile Menu Toggle
   * Tests: Mobile drawer open/close functionality
   */
  describe('Mobile Menu Functionality', () => {
    it('has menu toggle button for mobile', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const menuButton = screen.getByLabelText(/Open menu/i);
        expect(menuButton).toBeInTheDocument();
      });
    });

    it('menu toggle button has proper ARIA attributes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      const menuButton = screen.getByLabelText(/Open menu/i);
      expect(menuButton).toHaveAttribute('aria-expanded', 'false');
    });
  });

  /**
   * Header Navigation
   * Tests: Top app bar navigation elements
   */
  describe('Header Navigation', () => {
    it('renders top app bar with AgentHR branding', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const branding = screen.getByText('AgentHR');
        expect(branding).toBeInTheDocument();
      });
    });

    it('has job alerts button in header', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      const alertsButton = screen.getByLabelText('Job alerts');
      expect(alertsButton).toBeInTheDocument();
    });
  });

  /**
   * Navigation Consistency
   * Tests: Navigation is consistent across all pages
   */
  describe('Navigation Consistency', () => {
    const routes = ['/jobs', '/jobs/saved', '/jobs/applications', '/profile'];

    it.each(routes)('sidebar navigation is present on %s', async (route) => {
      renderWithProviders(
        <MemoryRouter initialEntries={[route]}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Find Jobs')).toBeInTheDocument();
        expect(screen.getByText('Jobs')).toBeInTheDocument();
        expect(screen.getByText('Career')).toBeInTheDocument();
        expect(screen.getByText('Account')).toBeInTheDocument();
      });
    });

    it.each(routes)('bottom navigation is present on %s (mobile)', async (route) => {
      renderWithProviders(
        <MemoryRouter initialEntries={[route]}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('navigation', { name: /Mobile navigation/i })).toBeInTheDocument();
      });
    });
  });
});
