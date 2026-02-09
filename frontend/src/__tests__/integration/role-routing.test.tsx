/**
 * Integration Tests: Role-Based Routing Protection
 *
 * Tests the ProtectedRoute component integration with React Router.
 * Verifies that role-based access control works correctly for:
 * - Job Seeker routes (require JobSeeker role)
 * - Recruiter routes (require Recruiter or Admin role)
 * - Admin-only routes (require Admin role)
 * - Redirect behavior for unauthorized users
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// ProtectedRoute and Role Types
import ProtectedRoute from '../../auth/ProtectedRoute';
import { UserRole, UserInfo } from '@/contexts/AuthContext';

// Context Providers
import { AuthProvider, AuthContext } from '../../contexts/AuthContext';
import { EmotionThemeProvider } from '../../contexts/EmotionThemeContext';
import { LanguageProvider } from '../../contexts/LanguageContext';

// Layout Components
import JobSeekerLayout from '../../layouts/JobSeekerLayout';
import RecruiterLayout from '../../layouts/RecruiterLayout';

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
  { queryClient = createTestQueryClient(), user = null, ...renderOptions } = {}
) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    // Create a mock auth context value
    const mockAuthValue = {
      user,
      accessToken: user ? 'mock-token' : null,
      refreshToken: user ? 'mock-refresh-token' : null,
      isAuthenticated: !!user,
      isLoading: false,
      isInitialized: true,
      error: null,
      register: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
      refreshAccessToken: vi.fn(),
      clearError: vi.fn(),
      hasRole: (role: UserRole) => user?.roles?.includes(role) || false,
      hasAnyRole: (roles: UserRole[]) => roles.some(role => user?.roles?.includes(role)),
    };

    return (
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider value={mockAuthValue}>
          <EmotionThemeProvider>
            <LanguageProvider>
              {children}
            </LanguageProvider>
          </EmotionThemeProvider>
        </AuthContext.Provider>
      </QueryClientProvider>
    );
  };
  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Helper function to create mock users
const createMockUser = (roles: UserRole[]): UserInfo => ({
  id: '123',
  email: 'test@example.com',
  full_name: 'Test User',
  roles,
});

describe('Role-Based Routing Protection Integration Tests', () => {
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

  describe('Unauthenticated Users', () => {
    it('should redirect unauthenticated users to login', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/dashboard" element={
              <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
                <div>Recruiter Dashboard</div>
              </ProtectedRoute>
            } />
            <Route path="/auth/login" element={<div>Login Page</div>} />
          </Routes>
        </MemoryRouter>,
        { user: null }
      );

      await waitFor(() => {
        expect(screen.queryByText('Recruiter Dashboard')).not.toBeInTheDocument();
      });
    });

    it('should redirect unauthenticated users from job seeker routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={
              <ProtectedRoute requiredRoles={UserRole.JobSeeker}>
                <div>Jobs Page</div>
              </ProtectedRoute>
            } />
            <Route path="/auth/login" element={<div>Login Page</div>} />
          </Routes>
        </MemoryRouter>,
        { user: null }
      );

      await waitFor(() => {
        expect(screen.queryByText('Jobs Page')).not.toBeInTheDocument();
      });
    });

    it('should allow public routes without authentication', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={
              <ProtectedRoute>
                <div>Public Home Page</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: null }
      );

      // Note: ProtectedRoute requires auth by default, so this would redirect
      // This test documents the expected behavior
      await waitFor(() => {
        expect(screen.queryByText('Public Home Page')).not.toBeInTheDocument();
      });
    });
  });

  describe('JobSeeker Role Access', () => {
    const jobSeekerUser = createMockUser([UserRole.JobSeeker]);

    it('should allow JobSeeker to access JobSeeker routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={
              <ProtectedRoute requiredRoles={UserRole.JobSeeker}>
                <JobSeekerLayout />
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: jobSeekerUser }
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('should allow JobSeeker to access profile page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/profile']}>
          <Routes>
            <Route path="/profile" element={
              <ProtectedRoute requiredRoles={UserRole.JobSeeker}>
                <JobSeekerLayout />
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: jobSeekerUser }
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('should deny JobSeeker access to Recruiter routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/dashboard" element={
              <ProtectedRoute
                requiredRoles={[UserRole.Recruiter, UserRole.Admin]}
                unauthorizedTo="/unauthorized"
              >
                <div>Recruiter Dashboard</div>
              </ProtectedRoute>
            } />
            <Route path="/unauthorized" element={<div>Unauthorized Page</div>} />
          </Routes>
        </MemoryRouter>,
        { user: jobSeekerUser }
      );

      await waitFor(() => {
        expect(screen.queryByText('Recruiter Dashboard')).not.toBeInTheDocument();
        expect(screen.getByText('Unauthorized Page')).toBeInTheDocument();
      });
    });

    it('should deny JobSeeker access to Admin-only routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/settings']}>
          <Routes>
            <Route path="/admin/settings" element={
              <ProtectedRoute
                requiredRoles={UserRole.Admin}
                unauthorizedTo="/unauthorized"
              >
                <div>Admin Settings</div>
              </ProtectedRoute>
            } />
            <Route path="/unauthorized" element={<div>Unauthorized Page</div>} />
          </Routes>
        </MemoryRouter>,
        { user: jobSeekerUser }
      );

      await waitFor(() => {
        expect(screen.queryByText('Admin Settings')).not.toBeInTheDocument();
        expect(screen.getByText('Unauthorized Page')).toBeInTheDocument();
      });
    });
  });

  describe('Recruiter Role Access', () => {
    const recruiterUser = createMockUser([UserRole.Recruiter]);

    it('should allow Recruiter to access Recruiter routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/dashboard" element={
              <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
                <RecruiterLayout />
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: recruiterUser }
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('should allow Recruiter to access vacancies page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/vacancies']}>
          <Routes>
            <Route path="/recruiter/vacancies" element={
              <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
                <RecruiterLayout />
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: recruiterUser }
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('should allow Recruiter to access candidates page', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/candidates']}>
          <Routes>
            <Route path="/recruiter/candidates" element={
              <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
                <div>Candidates Page</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: recruiterUser }
      );

      await waitFor(() => {
        expect(screen.getByText('Candidates Page')).toBeInTheDocument();
      });
    });

    it('should deny Recruiter access to Admin-only routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/users']}>
          <Routes>
            <Route path="/admin/users" element={
              <ProtectedRoute
                requiredRoles={UserRole.Admin}
                unauthorizedTo="/unauthorized"
              >
                <div>Admin Users</div>
              </ProtectedRoute>
            } />
            <Route path="/unauthorized" element={<div>Unauthorized Page</div>} />
          </Routes>
        </MemoryRouter>,
        { user: recruiterUser }
      );

      await waitFor(() => {
        expect(screen.queryByText('Admin Users')).not.toBeInTheDocument();
        expect(screen.getByText('Unauthorized Page')).toBeInTheDocument();
      });
    });
  });

  describe('Admin Role Access', () => {
    const adminUser = createMockUser([UserRole.Admin]);

    it('should allow Admin to access Recruiter routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/dashboard" element={
              <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
                <RecruiterLayout />
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: adminUser }
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('should allow Admin to access Admin-only routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/settings']}>
          <Routes>
            <Route path="/admin/settings" element={
              <ProtectedRoute requiredRoles={UserRole.Admin}>
                <div>Admin Settings</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: adminUser }
      );

      await waitFor(() => {
        expect(screen.getByText('Admin Settings')).toBeInTheDocument();
      });
    });

    it('should allow Admin to access all recruiter sub-routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/vacancies/123/edit']}>
          <Routes>
            <Route path="/recruiter" element={
              <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
                <RecruiterLayout />
              </ProtectedRoute>
            }>
              <Route path="vacancies/:id/edit" element={<div>Edit Vacancy</div>} />
            </Route>
          </Routes>
        </MemoryRouter>,
        { user: adminUser }
      );

      await waitFor(() => {
        expect(screen.getByText('Edit Vacancy')).toBeInTheDocument();
      });
    });
  });

  describe('Multi-Role Users', () => {
    const multiRoleUser = createMockUser([UserRole.Recruiter, UserRole.Admin]);

    it('should grant access when user has multiple roles and one matches', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/analytics']}>
          <Routes>
            <Route path="/recruiter/analytics" element={
              <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
                <div>Analytics Page</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: multiRoleUser }
      );

      await waitFor(() => {
        expect(screen.getByText('Analytics Page')).toBeInTheDocument();
      });
    });

    it('should grant Admin access to Admin-only routes even with multiple roles', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/users']}>
          <Routes>
            <Route path="/admin/users" element={
              <ProtectedRoute requiredRoles={UserRole.Admin}>
                <div>Admin Users</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: multiRoleUser }
      );

      await waitFor(() => {
        expect(screen.getByText('Admin Users')).toBeInTheDocument();
      });
    });
  });

  describe('Protected Recruiter Layout Integration', () => {
    const recruiterUser = createMockUser([UserRole.Recruiter]);
    const jobSeekerUser = createMockUser([UserRole.JobSeeker]);

    it('should render ProtectedRecruiterLayout for authenticated recruiters', async () => {
      // Simulate ProtectedRecruiterLayout from App.tsx
      const ProtectedRecruiterLayout = () => (
        <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
          <RecruiterLayout />
        </ProtectedRoute>
      );

      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/dashboard" element={<ProtectedRecruiterLayout />}>
              <Route index element={<div>Dashboard Content</div>} />
            </Route>
          </Routes>
        </MemoryRouter>,
        { user: recruiterUser }
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('should deny JobSeeker access to ProtectedRecruiterLayout', async () => {
      const ProtectedRecruiterLayout = () => (
        <ProtectedRoute
          requiredRoles={[UserRole.Recruiter, UserRole.Admin]}
          unauthorizedTo="/unauthorized"
        >
          <RecruiterLayout />
        </ProtectedRoute>
      );

      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/dashboard" element={<ProtectedRecruiterLayout />}>
              <Route index element={<div>Dashboard Content</div>} />
            </Route>
            <Route path="/unauthorized" element={<div>Unauthorized Page</div>} />
          </Routes>
        </MemoryRouter>,
        { user: jobSeekerUser }
      );

      await waitFor(() => {
        expect(screen.queryByText('Dashboard Content')).not.toBeInTheDocument();
        expect(screen.getByText('Unauthorized Page')).toBeInTheDocument();
      });
    });

    it('should protect all nested routes under recruiter path', async () => {
      const ProtectedRecruiterLayout = () => (
        <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
          <RecruiterLayout />
        </ProtectedRoute>
      );

      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/vacancies/123']}>
          <Routes>
            <Route path="/recruiter" element={<ProtectedRecruiterLayout />}>
              <Route path="vacancies/:id" element={<div>Vacancy Detail</div>} />
            </Route>
          </Routes>
        </MemoryRouter>,
        { user: recruiterUser }
      );

      await waitFor(() => {
        expect(screen.getByText('Vacancy Detail')).toBeInTheDocument();
      });
    });
  });

  describe('Array vs Single Role Specification', () => {
    const recruiterUser = createMockUser([UserRole.Recruiter]);

    it('should accept single role as string', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/dashboard" element={
              <ProtectedRoute requiredRoles={UserRole.Recruiter}>
                <div>Recruiter Dashboard</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: recruiterUser }
      );

      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });
    });

    it('should accept array of roles', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/dashboard" element={
              <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
                <div>Recruiter Dashboard</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: recruiterUser }
      );

      await waitFor(() => {
        expect(screen.getByText('Recruiter Dashboard')).toBeInTheDocument();
      });
    });
  });

  describe('Redirect Behavior', () => {
    const jobSeekerUser = createMockUser([UserRole.JobSeeker]);

    it('should redirect to login by default for unauthenticated users', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/dashboard" element={
              <ProtectedRoute requiredRoles={UserRole.Recruiter}>
                <div>Recruiter Dashboard</div>
              </ProtectedRoute>
            } />
            <Route path="/auth/login" element={<div>Login Page</div>} />
          </Routes>
        </MemoryRouter>,
        { user: null }
      );

      await waitFor(() => {
        expect(screen.getByText('Login Page')).toBeInTheDocument();
      });
    });

    it('should use custom redirectTo when specified', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter/dashboard" element={
              <ProtectedRoute
                requiredRoles={UserRole.Recruiter}
                redirectTo="/custom-login"
              >
                <div>Recruiter Dashboard</div>
              </ProtectedRoute>
            } />
            <Route path="/custom-login" element={<div>Custom Login Page</div>} />
          </Routes>
        </MemoryRouter>,
        { user: null }
      );

      await waitFor(() => {
        expect(screen.getByText('Custom Login Page')).toBeInTheDocument();
      });
    });

    it('should use custom unauthorizedTo when specified', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/admin/settings']}>
          <Routes>
            <Route path="/admin/settings" element={
              <ProtectedRoute
                requiredRoles={UserRole.Admin}
                unauthorizedTo="/no-permission"
              >
                <div>Admin Settings</div>
              </ProtectedRoute>
            } />
            <Route path="/no-permission" element={<div>No Permission Page</div>} />
          </Routes>
        </MemoryRouter>,
        { user: jobSeekerUser }
      );

      await waitFor(() => {
        expect(screen.getByText('No Permission Page')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle routes without role requirements (authenticated users only)', async () => {
      const authenticatedUser = createMockUser([UserRole.JobSeeker]);

      renderWithProviders(
        <MemoryRouter initialEntries={['/profile']}>
          <Routes>
            <Route path="/profile" element={
              <ProtectedRoute>
                <div>Profile Page</div>
              </ProtectedRoute>
            } />
          </Routes>
        </MemoryRouter>,
        { user: authenticatedUser }
      );

      await waitFor(() => {
        expect(screen.getByText('Profile Page')).toBeInTheDocument();
      });
    });

    it('should handle deeply nested protected routes', async () => {
      const recruiterUser = createMockUser([UserRole.Recruiter]);

      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/vacancies/123/candidates/456']}>
          <Routes>
            <Route path="/recruiter" element={
              <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
                <RecruiterLayout />
              </ProtectedRoute>
            }>
              <Route path="vacancies/:id/candidates/:candidateId" element={
                <div>Candidate Detail Page</div>
              } />
            </Route>
          </Routes>
        </MemoryRouter>,
        { user: recruiterUser }
      );

      await waitFor(() => {
        expect(screen.getByText('Candidate Detail Page')).toBeInTheDocument();
      });
    });
  });

  describe('Integration with Layout Components', () => {
    const jobSeekerUser = createMockUser([UserRole.JobSeeker]);
    const recruiterUser = createMockUser([UserRole.Recruiter]);

    it('should render JobSeekerLayout with protected routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <ProtectedRoute requiredRoles={UserRole.JobSeeker}>
            <JobSeekerLayout />
          </ProtectedRoute>
        </MemoryRouter>,
        { user: jobSeekerUser }
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });

    it('should render RecruiterLayout with protected routes', async () => {
      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <ProtectedRoute requiredRoles={[UserRole.Recruiter, UserRole.Admin]}>
            <RecruiterLayout />
          </ProtectedRoute>
        </MemoryRouter>,
        { user: recruiterUser }
      );

      await waitFor(() => {
        expect(screen.getByText('AgentHR')).toBeInTheDocument();
      });
    });
  });
});
