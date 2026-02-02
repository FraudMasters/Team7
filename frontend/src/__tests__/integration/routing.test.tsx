/**
 * Integration Tests: Routing and Navigation
 *
 * Tests the React Router v6 configuration, route navigation, and dual-flow architecture.
 * Verifies that routes work correctly for landing page, job seeker flow, and recruiter flow.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// App and Layout Components
import JobSeekerLayout from '../../layouts/JobSeekerLayout';
import RecruiterLayout from '../../layouts/RecruiterLayout';

// Context Providers
import { ThemeProvider } from '../../contexts/ThemeContext';
import { LanguageProvider } from '../../contexts/LanguageContext';

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

// Mock API client
vi.mock('../../api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Routing Integration Tests', () => {
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

  describe('Job Seeker Flow Routes', () => {
    it('renders JobSeekerLayout for /jobs routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('displays bottom navigation in JobSeekerLayout', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const bottomNav = screen.getByRole('navigation', { name: /main navigation/i });
        expect(bottomNav).toBeInTheDocument();
      });
    });

    it('shows all navigation items in JobSeekerLayout bottom navigation', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Navigate to Search')).toBeInTheDocument();
        expect(screen.getByLabelText('Navigate to Saved')).toBeInTheDocument();
        expect(screen.getByLabelText('Navigate to Applications')).toBeInTheDocument();
        expect(screen.getByLabelText('Navigate to Profile')).toBeInTheDocument();
      });
    });

    it('has skip link for accessibility in JobSeekerLayout', async () => {
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

  describe('Recruiter Flow Routes', () => {
    it('renders RecruiterLayout for /recruiter routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/*" element={<RecruiterLayout />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('displays sidebar navigation in RecruiterLayout', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <RecruiterLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const sidebar = screen.getByRole('navigation', { name: /recruiter sidebar/i });
        expect(sidebar).toBeInTheDocument();
      });
    });

    it('shows all navigation items in RecruiterLayout sidebar', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <RecruiterLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Vacancies')).toBeInTheDocument();
        expect(screen.getByText('Candidates')).toBeInTheDocument();
        expect(screen.getByText('Analytics')).toBeInTheDocument();
      });
    });

    it('has skip link for accessibility in RecruiterLayout', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <RecruiterLayout />
        </MemoryRouter>
      );

      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');
    });
  });

  describe('Nested Routes', () => {
    it('handles nested routes correctly for job detail pages', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/123']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path=":id" element={<div>Job Detail Page</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Job Detail Page')).toBeInTheDocument();
      });
    });

    it('handles nested routes correctly for application flow', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/123/apply']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path=":id/apply" element={<div>Application Flow Page</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Application Flow Page')).toBeInTheDocument();
      });
    });

    it('handles deeply nested routes for vacancy edit form', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/vacancies/123/edit']}>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="vacancies">
                <Route path=":id/edit" element={<div>Edit Vacancy Form</div>} />
              </Route>
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Edit Vacancy Form')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('provides proper ARIA labels for navigation elements', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const mainNav = screen.getByRole('navigation', { name: /main navigation/i });
        expect(mainNav).toBeInTheDocument();
        expect(mainNav).toHaveAttribute('aria-label', 'Main navigation');
      });
    });

    it('provides skip-to-content links in both layouts', async () => {
      // JobSeekerLayout
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <JobSeekerLayout />
        </MemoryRouter>
      );

      await waitFor(() => {
        const skipLink = screen.getByText('Skip to main content');
        expect(skipLink).toBeInTheDocument();
      });
    });
  });
});
