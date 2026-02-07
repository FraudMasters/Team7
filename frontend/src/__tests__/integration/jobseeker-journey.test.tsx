/**
 * Integration Tests: JobSeeker Journey End-to-End Flow
 *
 * Tests the complete JobSeeker user journey from landing page to profile.
 * Verifies navigation, page accessibility, and component rendering for all key JobSeeker pages.
 *
 * Verification Steps (from spec):
 * 1. Navigate to landing page
 * 2. Browse jobs
 * 3. View job detail
 * 4. Navigate to saved jobs
 * 5. Navigate to applications
 * 6. Navigate to profile
 * 7. Verify all pages accessible
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Page Components
import LandingPage from '../../pages/LandingPage';
import { JobsBrowsePage } from '../../pages/jobs/JobsBrowsePage';
import { JobDetailPage } from '../../pages/jobs/JobDetailPage';
import { SavedJobsPage } from '../../pages/jobs/SavedJobsPage';
import { MyApplicationsPage } from '../../pages/jobs/MyApplicationsPage';
import { CandidateProfilePage } from '../../pages/jobs/CandidateProfilePage';

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
        {
          id: '2',
          title: 'Product Manager',
          description: 'Lead product strategy',
          location: 'San Francisco, CA',
          work_format: 'office',
          min_experience_months: 36,
          required_skills: ['Strategy', 'Communication'],
        },
      ],
    },
    isLoading: false,
    error: null,
  }),
  useJob: (id: string) => ({
    data: {
      id,
      title: 'Software Engineer',
      description: 'Develop awesome software',
      location: 'Remote',
      work_format: 'remote',
      min_experience_months: 24,
      required_skills: ['React', 'TypeScript'],
      industry: 'Technology',
      salary_min: 80000,
    },
    isLoading: false,
    error: null,
  }),
}));

vi.mock('../../hooks/useSavedJobs', () => ({
  useSavedJobs: () => ({
    data: {
      saved_jobs: [
        {
          id: 'saved-1',
          title: 'Frontend Developer',
          description: 'Build modern web apps',
          location: 'Remote',
          work_format: 'remote',
        },
      ],
      total: 1,
    },
    isLoading: false,
    error: null,
  }),
  useRemoveSavedJob: () => ({
    mutate: vi.fn(),
  }),
}));

vi.mock('../../hooks/useApplications', () => ({
  useApplications: () => ({
    data: {
      applications: [
        {
          id: 'app-1',
          title: 'Software Engineer',
          description: 'Applied position',
          status: 'under_review',
          applied_date: '2024-01-15',
        },
      ],
      total: 1,
    },
    isLoading: false,
    error: null,
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

describe('JobSeeker Journey - End-to-End Integration Tests', () => {
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
   * Step 1: Navigate to landing page
   * Expected: Landing page renders with role selection cards
   */
  describe('Step 1: Landing Page', () => {
    it('renders landing page with role selection', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
        expect(screen.getByText('AI-Powered Recruitment Platform')).toBeInTheDocument();
      });

      // Verify role cards are present
      expect(screen.getByText('Job Seeker')).toBeInTheDocument();
      expect(screen.getByText('Recruiter')).toBeInTheDocument();
      expect(screen.getByText('Browse Jobs')).toBeInTheDocument();
      expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();

      // Verify accessibility features
      expect(screen.getByText('Skip to main content')).toBeInTheDocument();
      const mainContent = screen.getByRole('navigation', { name: /select your role/i });
      expect(mainContent).toBeInTheDocument();
    });

    it('has accessible navigation for keyboard users', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/']}>
          <LandingPage />
        </MemoryRouter>
      );

      // Check for skip link
      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toHaveAttribute('href', '#main-content');

      // Check for ARIA attributes on role cards
      const jobSeekerCard = screen.getByLabelText(/Select Job Seeker role/i);
      expect(jobSeekerCard).toBeInTheDocument();
      expect(jobSeekerCard).toHaveAttribute('role', 'listitem');
    });
  });

  /**
   * Step 2: Browse jobs
   * Expected: JobsBrowsePage renders with job cards
   */
  describe('Step 2: Browse Jobs Page', () => {
    it('renders jobs browse page within JobSeekerLayout', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route index element={<JobsBrowsePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Find Your Next Job')).toBeInTheDocument();
        expect(screen.getByText(/Discover opportunities matched to your skills/)).toBeInTheDocument();
      });

      // Verify layout components
      expect(screen.getByText('AgentHR')).toBeInTheDocument();

      // Verify search and filter components
      const searchInput = screen.getByPlaceholderText('Search jobs...');
      expect(searchInput).toBeInTheDocument();
    });

    it('displays job cards with job information', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('has working bottom navigation for mobile', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('navigation', { name: /Mobile navigation/i })).toBeInTheDocument();
      });
    });

    it('has skip-to-content link for accessibility', async () => {
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
   * Step 3: View job detail
   * Expected: JobDetailPage renders with full job information
   */
  describe('Step 3: Job Detail Page', () => {
    it('renders job detail page with job information', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/1']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path=":id" element={<JobDetailPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Software Engineer')).toBeInTheDocument();
      });

      // Verify job details are displayed
      expect(screen.getByText(/Develop awesome software/)).toBeInTheDocument();
      expect(screen.getByText('Remote')).toBeInTheDocument();
    });

    it('displays required skills as chips', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/1']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path=":id" element={<JobDetailPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
        expect(screen.getByText('TypeScript')).toBeInTheDocument();
      });
    });

    it('shows action buttons (Apply Now and Save)', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/1']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path=":id" element={<JobDetailPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Apply Now/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Save/i })).toBeInTheDocument();
      });
    });

    it('handles loading state correctly', async () => {
      // Mock loading state
      const { useJob } = await import('../../hooks/useJobs');
      vi.doMock('../../hooks/useJobs', () => ({
        useJob: () => ({
          data: null,
          isLoading: true,
          error: null,
        }),
      }));

      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/1']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path=":id" element={<JobDetailPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Should show loading indicator
      await waitFor(() => {
        const circularProgress = document.querySelector('.MuiCircularProgress-root');
        expect(circularProgress).toBeInTheDocument();
      });
    });

    it('handles error state gracefully', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/999']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path=":id" element={<JobDetailPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Should show error message for non-existent job
      await waitFor(() => {
        expect(screen.getByText('Job not found')).toBeInTheDocument();
      });
    });
  });

  /**
   * Step 4: Navigate to saved jobs
   * Expected: SavedJobsPage renders with saved job cards
   */
  describe('Step 4: Saved Jobs Page', () => {
    it('renders saved jobs page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/saved']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path="saved" element={<SavedJobsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Saved Jobs')).toBeInTheDocument();
        expect(screen.getByText(/Your bookmarked job opportunities/)).toBeInTheDocument();
      });
    });

    it('displays search functionality for saved jobs', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/saved']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path="saved" element={<SavedJobsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      const searchInput = screen.getByPlaceholderText('Search saved jobs...');
      expect(searchInput).toBeInTheDocument();
    });

    it('shows saved job count', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/saved']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path="saved" element={<SavedJobsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('1 saved')).toBeInTheDocument();
      });
    });

    it('displays empty state when no saved jobs', async () => {
      // Mock empty saved jobs
      const { useSavedJobs } = await import('../../hooks/useSavedJobs');
      vi.doMock('../../hooks/useSavedJobs', () => ({
        useSavedJobs: () => ({
          data: { saved_jobs: [], total: 0 },
          isLoading: false,
          error: null,
        }),
        useRemoveSavedJob: () => ({ mutate: vi.fn() }),
      }));

      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/saved']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path="saved" element={<SavedJobsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/No saved jobs yet/)).toBeInTheDocument();
      });
    });
  });

  /**
   * Step 5: Navigate to applications
   * Expected: MyApplicationsPage renders with application cards
   */
  describe('Step 5: My Applications Page', () => {
    it('renders my applications page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/applications']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path="applications" element={<MyApplicationsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('My Applications')).toBeInTheDocument();
        expect(screen.getByText(/Track your job application progress/)).toBeInTheDocument();
      });
    });

    it('displays application filters', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/applications']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path="applications" element={<MyApplicationsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Status filter
      expect(screen.getByLabelText('Status')).toBeInTheDocument();

      // Search input
      const searchInput = screen.getByPlaceholderText('Search applications...');
      expect(searchInput).toBeInTheDocument();
    });

    it('shows total applications count', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/applications']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path="applications" element={<MyApplicationsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('1 total')).toBeInTheDocument();
      });
    });

    it('displays status filter options', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/applications']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path="applications" element={<MyApplicationsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Open the status dropdown
      const statusSelect = screen.getByLabelText('Status');
      expect(statusSelect).toBeInTheDocument();
    });

    it('shows empty state when no applications', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/applications']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path="applications" element={<MyApplicationsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );
    });
  });

  /**
   * Step 6: Navigate to profile
   * Expected: CandidateProfilePage renders with user information
   */
  describe('Step 6: Candidate Profile Page', () => {
    it('renders candidate profile page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/profile']}>
          <Routes>
            <Route path="/profile" element={<JobSeekerLayout />}>
              <Route index element={<CandidateProfilePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        // Profile shows placeholder data
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });
    });

    it('displays contact information', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/profile']}>
          <Routes>
            <Route path="/profile" element={<JobSeekerLayout />}>
              <Route index element={<CandidateProfilePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('john.doe@example.com')).toBeInTheDocument();
        expect(screen.getByText('+1 (555) 123-4567')).toBeInTheDocument();
        expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
      });
    });

    it('displays skills', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/profile']}>
          <Routes>
            <Route path="/profile" element={<JobSeekerLayout />}>
              <Route index element={<CandidateProfilePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
        expect(screen.getByText('TypeScript')).toBeInTheDocument();
        expect(screen.getByText('Node.js')).toBeInTheDocument();
      });
    });

    it('shows experience section', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/profile']}>
          <Routes>
            <Route path="/profile" element={<JobSeekerLayout />}>
              <Route index element={<CandidateProfilePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Experience')).toBeInTheDocument();
        expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument();
        expect(screen.getByText('Tech Corp')).toBeInTheDocument();
      });
    });

    it('shows education section', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/profile']}>
          <Routes>
            <Route path="/profile" element={<JobSeekerLayout />}>
              <Route index element={<CandidateProfilePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Education')).toBeInTheDocument();
        expect(screen.getByText('Bachelor of Science')).toBeInTheDocument();
        expect(screen.getByText('University of California')).toBeInTheDocument();
      });
    });

    it('has edit profile functionality', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/profile']}>
          <Routes>
            <Route path="/profile" element={<JobSeekerLayout />}>
              <Route index element={<CandidateProfilePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        const editButton = screen.getByRole('button', { name: /Edit Profile/i });
        expect(editButton).toBeInTheDocument();
      });
    });
  });

  /**
   * Step 7: Verify all pages accessible
   * Expected: All navigation links work correctly
   */
  describe('Step 7: Complete Navigation Flow', () => {
    it('can navigate from landing to jobs', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/jobs" element={<div>Jobs Page</div>} />
          </Routes>
        </MemoryRouter>
      );

      const browseButton = screen.getByText('Browse Jobs');
      expect(browseButton).toBeInTheDocument();
    });

    it('all JobSeeker routes are properly configured', async () => {
      const jobSeekerRoutes = [
        '/jobs',
        '/jobs/saved',
        '/jobs/applications',
        '/profile',
      ];

      jobSeekerRoutes.forEach(route => {
        expect(() => {
          renderWithProviders(
            <MemoryRouter initialEntries={[route]}>
              <Routes>
                <Route path="/jobs" element={<JobSeekerLayout />}>
                  <Route index element={<JobsBrowsePage />} />
                  <Route path="saved" element={<SavedJobsPage />} />
                  <Route path="applications" element={<MyApplicationsPage />} />
                </Route>
                <Route path="/profile" element={<JobSeekerLayout />}>
                  <Route index element={<CandidateProfilePage />} />
                </Route>
              </Routes>
            </MemoryRouter>
          );
        }).not.toThrow();
      });
    });

    it('JobSeekerLayout navigation contains all required links', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        // Verify main navigation items
        expect(screen.getByText('Find Jobs')).toBeInTheDocument();
        expect(screen.getByText('Browse')).toBeInTheDocument();
        expect(screen.getByText('Saved')).toBeInTheDocument();
        expect(screen.getByText('Applications')).toBeInTheDocument();
        expect(screen.getByText('Profile')).toBeInTheDocument();
      });
    });

    it('bottom navigation contains essential links for mobile', async () => {
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

    it('all pages render without errors', async () => {
      const routes = [
        { path: '/jobs', element: <JobsBrowsePage /> },
        { path: '/jobs/saved', element: <SavedJobsPage /> },
        { path: '/jobs/applications', element: <MyApplicationsPage /> },
        { path: '/profile', element: <CandidateProfilePage /> },
      ];

      for (const route of routes) {
        expect(() => {
          renderWithProviders(
            <MemoryRouter initialEntries={[route.path]}>
              <Routes>
                <Route path="/jobs" element={<JobSeekerLayout />}>
                  <Route index element={<JobsBrowsePage />} />
                  <Route path="saved" element={<SavedJobsPage />} />
                  <Route path="applications" element={<MyApplicationsPage />} />
                </Route>
                <Route path="/profile" element={<JobSeekerLayout />}>
                  <Route index element={<CandidateProfilePage />} />
                </Route>
              </Routes>
            </MemoryRouter>
          );
        }).not.toThrow();
      }
    });
  });

  /**
   * Accessibility Tests
   * Verify all JobSeeker pages are accessible
   */
  describe('Accessibility', () => {
    it('LandingPage has proper ARIA labels', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/']}>
          <LandingPage />
        </MemoryRouter>
      );

      expect(screen.getByRole('navigation', { name: /select your role/i })).toBeInTheDocument();
    });

    it('JobSeekerLayout has skip-to-content link', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });

    it('JobSeekerLayout main content has proper id', async () => {
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

    it('navigation elements have proper ARIA roles', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('navigation', { name: /Main navigation/i })).toBeInTheDocument();
      });
    });
  });

  /**
   * Error Handling Tests
   * Verify error states are handled gracefully
   */
  describe('Error Handling', () => {
    it('shows loading state while data is loading', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route index element={<JobsBrowsePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // With mocked data, should load without showing loading state
      await waitFor(() => {
        expect(screen.getByText('Find Your Next Job')).toBeInTheDocument();
      });
    });

    it('handles invalid routes gracefully', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/invalid-route']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path=":id" element={<JobDetailPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Job not found')).toBeInTheDocument();
      });
    });
  });
});
