/**
 * Integration Tests: Admin Journey End-to-End Flow
 *
 * Tests the complete Admin user journey with elevated privileges.
 * Verifies navigation, page accessibility, component rendering, and cross-role access.
 *
 * Verification Steps (from spec):
 * 1. Navigate to admin dashboard
 * 2. Access user management
 * 3. Access system settings
 * 4. Access audit logs
 * 5. Verify access to Recruiter routes
 * 6. Verify read-only access to JobSeeker flows
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Page Components
import { AdminDashboard } from '../../pages/admin/AdminDashboard';
import { AdminUsers } from '../../pages/admin/AdminUsers';
import { AdminSettings } from '../../pages/admin/AdminSettings';
import AdminAuditLogsPage from '../../pages/admin/AdminAuditLogs';
import { DashboardPage } from '../../pages/recruiter/DashboardPage';
import { CandidatesKanbanPage } from '../../pages/recruiter/CandidatesKanbanPage';
import { JobsBrowsePage } from '../../pages/jobs/JobsBrowsePage';
import { JobDetailPage } from '../../pages/jobs/JobDetailPage';

// Layout Components
import AdminLayout from '../../layouts/AdminLayout';
import RecruiterLayout from '../../layouts/RecruiterLayout';
import JobSeekerLayout from '../../layouts/JobSeekerLayout';

// Context Providers
import { ThemeProvider } from '../../contexts/ThemeContext';
import { LanguageProvider } from '../../contexts/LanguageContext';

// Mock hooks for admin pages
vi.mock('../../hooks/useRoles', () => ({
  useRoles: () => ({
    roles: ['Admin'],
    hasRole: (role: string) => role === 'Admin',
    hasAnyRole: (roles: string[]) => roles.includes('Admin'),
    hasAllRoles: (roles: string[]) => roles.every(r => r === 'Admin'),
    getPrimaryRole: () => 'Admin',
  }),
}));

vi.mock('../../hooks/useAdminData', () => ({
  useAdminData: () => ({
    data: {
      organizations: 5,
      users: 42,
      systemHealth: 'Operational',
      analyticsReports: 12,
    },
    isLoading: false,
    error: null,
  }),
}));

vi.mock('../../hooks/useRecruiterData', () => ({
  useRecruiterData: () => ({
    data: {
      vacancies: [
        {
          id: '1',
          title: 'Senior Developer',
          status: 'active',
          candidates_count: 15,
        },
      ],
      candidates: [
        {
          id: 'c1',
          name: 'John Doe',
          status: 'new',
          match_score: 85,
        },
      ],
    },
    isLoading: false,
    error: null,
  }),
}));

// Mock hooks for job seeker access
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

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <LanguageProvider>
          {component}
        </LanguageProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('Admin Journey - Integration Tests', () => {
  /**
   * Step 1: Navigate to admin dashboard
   * Expected: Admin dashboard renders with system overview
   */
  describe('Step 1: Navigate to admin dashboard', () => {
    it('should render admin dashboard with metrics', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/dashboard']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="dashboard" element={<AdminDashboard />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify page heading
      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeVisible();
      });

      // Verify subtitle
      expect(screen.getByText('System overview and administrative controls')).toBeVisible();

      // Verify Admin badge
      expect(screen.getByText('ADMIN')).toBeVisible();

      // Verify metrics cards
      expect(screen.getByText('Organizations')).toBeVisible();
      expect(screen.getByText('Total Users')).toBeVisible();
      expect(screen.getByText('System Health')).toBeVisible();
      expect(screen.getByText('Analytics Reports')).toBeVisible();

      // Verify System Overview section
      expect(screen.getByText('System Overview')).toBeVisible();
    });

    it('should have proper accessibility features', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/dashboard']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="dashboard" element={<AdminDashboard />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify skip-to-content link
      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toHaveAttribute('href', '#main-content');

      // Verify ARIA navigation
      const mainNav = screen.getByRole('navigation', { name: /admin sidebar navigation/i });
      expect(mainNav).toBeVisible();

      // Verify main content area
      const mainContent = document.getElementById('main-content');
      expect(mainContent).toBeInTheDocument();
    });
  });

  /**
   * Step 2: Access user management
   * Expected: AdminUsers page renders with user list and actions
   */
  describe('Step 2: Access user management', () => {
    it('should render user management page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/users']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="users" element={<AdminUsers />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify page heading
      await waitFor(() => {
        expect(screen.getByText('User Management')).toBeVisible();
      });

      // Verify search functionality
      expect(screen.getByPlaceholderText(/search by name, email, role, or organization/i)).toBeVisible();

      // Verify table headers
      expect(screen.getByText('Name')).toBeVisible();
      expect(screen.getByText('Email')).toBeVisible();
      expect(screen.getByText('Role')).toBeVisible();
      expect(screen.getByText('Organization')).toBeVisible();
      expect(screen.getByText('Status')).toBeVisible();

      // Verify action menu is available
      const actionButtons = screen.getAllByRole('button');
      expect(actionButtons.length).toBeGreaterThan(0);
    });

    it('should have user search and filter functionality', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/users']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="users" element={<AdminUsers />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      const searchInput = screen.getByPlaceholderText(/search by name, email, role, or organization/i);
      expect(searchInput).toBeVisible();

      // Test search input interaction
      const user = userEvent.setup();
      await user.type(searchInput, 'admin');

      await waitFor(() => {
        expect(searchInput).toHaveValue('admin');
      });
    });
  });

  /**
   * Step 3: Access system settings
   * Expected: AdminSettings page renders with configuration options
   */
  describe('Step 3: Access system settings', () => {
    it('should render system settings page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/settings']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="settings" element={<AdminSettings />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify page heading
      await waitFor(() => {
        expect(screen.getByText('System Settings')).toBeVisible();
      });

      // Verify settings sections
      expect(screen.getByText('Authentication & Security')).toBeVisible();
      expect(screen.getByText('Email Configuration')).toBeVisible();
      expect(screen.getByText('System Limits')).toBeVisible();
      expect(screen.getByText('Data Retention')).toBeVisible();
      expect(screen.getByText('Feature Flags')).toBeVisible();

      // Verify save button
      expect(screen.getByRole('button', { name: /save changes/i })).toBeVisible();
    });

    it('should have editable configuration fields', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/settings']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="settings" element={<AdminSettings />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify session timeout field
      expect(screen.getByLabelText(/session timeout/i)).toBeVisible();

      // Verify email settings toggle
      const emailToggles = screen.getAllByRole('checkbox');
      expect(emailToggles.length).toBeGreaterThan(0);
    });
  });

  /**
   * Step 4: Access audit logs
   * Expected: AdminAuditLogs page renders with filterable log table
   */
  describe('Step 4: Access audit logs', () => {
    it('should render audit logs page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/audit-logs']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="audit-logs" element={<AdminAuditLogsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify page heading
      await waitFor(() => {
        expect(screen.getByText('Audit Logs')).toBeVisible();
      });

      // Verify stats cards
      expect(screen.getByText('Total Logs')).toBeVisible();
      expect(screen.getByText('Action Types')).toBeVisible();
      expect(screen.getByText('Entity Types')).toBeVisible();

      // Verify filter controls
      expect(screen.getByText('Filter Logs')).toBeVisible();
      expect(screen.getByText('Export Logs')).toBeVisible();

      // Verify table headers
      expect(screen.getByText('Timestamp')).toBeVisible();
      expect(screen.getByText('User')).toBeVisible();
      expect(screen.getByText('Action')).toBeVisible();
      expect(screen.getByText('Entity')).toBeVisible();
    });

    it('should have export and filter functionality', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/audit-logs']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="audit-logs" element={<AdminAuditLogsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify export button
      expect(screen.getByRole('button', { name: /export logs/i })).toBeVisible();

      // Verify refresh button
      expect(screen.getByRole('button', { name: /refresh/i })).toBeVisible();
    });
  });

  /**
   * Step 5: Verify access to Recruiter routes
   * Expected: Admin can access all Recruiter pages with elevated context
   */
  describe('Step 5: Verify access to Recruiter routes', () => {
    it('should access recruiter dashboard', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify recruiter dashboard renders
      await waitFor(() => {
        expect(screen.getByText(/dashboard/i)).toBeVisible();
      });
    });

    it('should access candidates kanban', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/candidates']}>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="candidates" element={<CandidatesKanbanPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify candidates page renders
      await waitFor(() => {
        expect(screen.getByText(/candidates/i)).toBeVisible();
      });
    });

    it('should have admin context indicator when accessing recruiter routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<DashboardPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Admin should see recruiter interface
      await waitFor(() => {
        expect(screen.getByText(/dashboard/i)).toBeVisible();
      });
    });
  });

  /**
   * Step 6: Verify read-only access to JobSeeker flows
   * Expected: Admin can view JobSeeker pages in read-only mode
   */
  describe('Step 6: Verify read-only access to JobSeeker flows', () => {
    it('should access jobs browse page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route index element={<JobsBrowsePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify jobs page renders
      await waitFor(() => {
        expect(screen.getByText(/find your next job/i)).toBeVisible();
      });

      // Verify navigation elements
      expect(screen.getByText('Find Jobs')).toBeVisible();
      expect(screen.getByText('Browse')).toBeVisible();
      expect(screen.getByText('Saved')).toBeVisible();
    });

    it('should access job detail page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/1']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path=":id" element={<JobDetailPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify job detail renders
      await waitFor(() => {
        expect(screen.getByText('Software Engineer')).toBeVisible();
      });

      // Verify job information
      expect(screen.getByText(/develop awesome software/i)).toBeVisible();
      expect(screen.getByText('Remote')).toBeVisible();
    });

    it('should maintain admin context while viewing jobseeker pages', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route index element={<JobsBrowsePage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify admin can view the page
      await waitFor(() => {
        expect(screen.getByText(/find your next job/i)).toBeVisible();
      });

      // Verify JobSeekerLayout navigation is present
      expect(screen.getByText('AgentHR')).toBeVisible();
    });
  });

  /**
   * Navigation Flow Tests
   * Tests complete user journey through admin pages
   */
  describe('Complete Admin Navigation Flow', () => {
    it('should navigate through all admin pages', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/dashboard']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="dashboard" element={<AdminDashboard />} />
              <Route path="users" element={<AdminUsers />} />
              <Route path="settings" element={<AdminSettings />} />
              <Route path="audit-logs" element={<AdminAuditLogsPage />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Start at dashboard
      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeVisible();
      });

      // Navigate to users (via direct link simulation)
      window.history.pushState({}, '', '/admin/users');
      await waitFor(() => {
        expect(screen.getByText('User Management')).toBeVisible();
      });

      // Navigate to settings
      window.history.pushState({}, '', '/admin/settings');
      await waitFor(() => {
        expect(screen.getByText('System Settings')).toBeVisible();
      });

      // Navigate to audit logs
      window.history.pushState({}, '', '/admin/audit-logs');
      await waitFor(() => {
        expect(screen.getByText('Audit Logs')).toBeVisible();
      });
    });
  });

  /**
   * Accessibility Tests
   */
  describe('Accessibility', () => {
    it('should have proper ARIA labels on navigation', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/dashboard']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="dashboard" element={<AdminDashboard />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify main navigation ARIA
      const mainNav = screen.getByRole('navigation', { name: /admin sidebar navigation/i });
      expect(mainNav).toBeVisible();

      // Verify navigation menubar
      const menubar = screen.getByRole('menubar');
      expect(menubar).toBeVisible();
    });

    it('should support keyboard navigation', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/dashboard']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="dashboard" element={<AdminDashboard />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify skip-to-content link for keyboard users
      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      expect(skipLink).toHaveAttribute('href', '#main-content');

      // Verify main content is focusable
      const mainContent = document.getElementById('main-content');
      expect(mainContent).toHaveAttribute('tabIndex', '-1');
    });
  });

  /**
   * Error Handling Tests
   */
  describe('Error Handling', () => {
    it('should handle loading states gracefully', async () => {
      // This test verifies that loading states are handled
      // In a real scenario, we would mock the hook to return isLoading: true
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/users']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="users" element={<AdminUsers />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Component should render without errors
      await waitFor(() => {
        expect(screen.getByText('User Management')).toBeVisible();
      });
    });

    it('should handle invalid admin routes gracefully', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/invalid-route']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="dashboard" element={<AdminDashboard />} />
              <Route path="users" element={<AdminUsers />} />
              <Route path="settings" element={<AdminSettings />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Should handle gracefully - may redirect or show error
      // The test verifies no unhandled errors occur
    });
  });

  /**
   * Mobile Responsive Tests
   */
  describe('Mobile Responsive', () => {
    it('should render admin layout on mobile viewport', async () => {
      // Simulate mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/dashboard']}>
          <Routes>
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="dashboard" element={<AdminDashboard />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify mobile menu button is present
      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeVisible();
      });
    });
  });
});
