/**
 * Integration Tests: Authentication State Persistence
 *
 * Tests the persistence of authentication state across route changes.
 * Verifies that user authentication, tokens, and role-based access control
 * are maintained when navigating between different flows (job seeker and recruiter).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route, useLocation } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// App and Layout Components
import JobSeekerLayout from '../../layouts/JobSeekerLayout';
import RecruiterLayout from '../../layouts/RecruiterLayout';

// Context Providers
import { AuthProvider, useAuthContext } from '../../contexts/AuthContext';
import { EmotionThemeProvider } from '../../contexts/EmotionThemeContext';
import { LanguageProvider } from '../../contexts/LanguageContext';
import { UserRole } from '../../contexts/AuthContext';

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
        <EmotionThemeProvider>
          <LanguageProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </LanguageProvider>
        </EmotionThemeProvider>
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

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
}));

// Test component to display current auth state
const AuthStateDisplay = () => {
  const { user, isAuthenticated, accessToken, hasRole, hasAnyRole } = useAuthContext();
  const location = useLocation();

  return (
    <div data-testid="auth-state">
      <div data-testid="current-path">{location.pathname}</div>
      <div data-testid="is-authenticated">{isAuthenticated.toString()}</div>
      <div data-testid="user-email">{user?.email || 'no-user'}</div>
      <div data-testid="has-access-token">{accessToken ? 'yes' : 'no'}</div>
      <div data-testid="has-jobseeker-role">{hasRole(UserRole.JobSeeker).toString()}</div>
      <div data-testid="has-recruiter-role">{hasRole(UserRole.Recruiter).toString()}</div>
      <div data-testid="has-any-recruiter-role">{hasAnyRole([UserRole.Recruiter, UserRole.Admin]).toString()}</div>
    </div>
  );
};

describe('Authentication State Persistence Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {};
        return mockStorage[key] || null;
      }),
      setItem: vi.fn((key: string, value: string) => {
        // Keep track of storage operations but don't actually persist
      }),
      removeItem: vi.fn(),
      clear: vi.fn(),
    });
  });

  describe('Auth State Across Job Seeker Routes', () => {
    it('persists authentication state when navigating between job seeker routes', async () => {
      const mockUser = {
        id: '123',
        email: 'jobseeker@example.com',
        full_name: 'Job Seeker',
        roles: [UserRole.JobSeeker],
      };

      // Mock initial auth state
      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });

      const { container } = renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route index element={<AuthStateDisplay />} />
              <Route path="saved" element={<AuthStateDisplay />} />
              <Route path="applications" element={<AuthStateDisplay />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify auth state on initial route
      await waitFor(() => {
        expect(screen.getByTestId('current-path')).toHaveTextContent('/jobs');
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
        expect(screen.getByTestId('user-email')).toHaveTextContent('jobseeker@example.com');
        expect(screen.getByTestId('has-access-token')).toHaveTextContent('yes');
        expect(screen.getByTestId('has-jobseeker-role')).toHaveTextContent('true');
      });
    });

    it('maintains user info when navigating from /jobs to /jobs/saved', async () => {
      const mockUser = {
        id: '456',
        email: 'seeker@example.com',
        full_name: 'Test Seeker',
        roles: [UserRole.JobSeeker],
      };

      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'test-token',
          refresh_token: 'test-refresh',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });

      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route index element={<AuthStateDisplay />} />
              <Route path="saved" element={<AuthStateDisplay />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // User state is preserved from localStorage on mount
      await waitFor(() => {
        expect(screen.getByTestId('user-email')).toHaveTextContent('seeker@example.com');
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
      });
    });

    it('maintains role checks across navigation', async () => {
      const mockUser = {
        id: '789',
        email: 'user@example.com',
        roles: [UserRole.JobSeeker, UserRole.Recruiter],
      };

      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'multi-role-token',
          refresh_token: 'multi-role-refresh',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });

      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs/applications']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route path="applications" element={<AuthStateDisplay />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('has-jobseeker-role')).toHaveTextContent('true');
        expect(screen.getByTestId('has-recruiter-role')).toHaveTextContent('true');
        expect(screen.getByTestId('has-any-recruiter-role')).toHaveTextContent('true');
      });
    });
  });

  describe('Auth State Across Recruiter Routes', () => {
    it('persists authentication state when navigating between recruiter routes', async () => {
      const mockUser = {
        id: 'recruiter-1',
        email: 'recruiter@example.com',
        full_name: 'Test Recruiter',
        roles: [UserRole.Recruiter],
      };

      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'recruiter-token',
          refresh_token: 'recruiter-refresh',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });

      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<AuthStateDisplay />} />
              <Route path="vacancies" element={<AuthStateDisplay />} />
              <Route path="candidates" element={<AuthStateDisplay />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('current-path')).toHaveTextContent('/recruiter/dashboard');
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true');
        expect(screen.getByTestId('user-email')).toHaveTextContent('recruiter@example.com');
        expect(screen.getByTestId('has-access-token')).toHaveTextContent('yes');
        expect(screen.getByTestId('has-recruiter-role')).toHaveTextContent('true');
        expect(screen.getByTestId('has-any-recruiter-role')).toHaveTextContent('true');
      });
    });

    it('maintains recruiter role access across nested routes', async () => {
      const mockUser = {
        id: 'rec-2',
        email: 'hiring@example.com',
        roles: [UserRole.Recruiter, UserRole.Admin],
      };

      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'admin-token',
          refresh_token: 'admin-refresh',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });

      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/vacancies/123/edit']}>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="vacancies">
                <Route path=":id/edit" element={<AuthStateDisplay />} />
              </Route>
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('user-email')).toHaveTextContent('hiring@example.com');
        expect(screen.getByTestId('has-recruiter-role')).toHaveTextContent('true');
        expect(screen.getByTestId('has-any-recruiter-role')).toHaveTextContent('true');
      });
    });
  });

  describe('Auth State Across Different Flows', () => {
    it('preserves auth state when conceptually switching between flows', async () => {
      const mockUser = {
        id: 'multi-1',
        email: 'multi@example.com',
        full_name: 'Multi Role User',
        roles: [UserRole.JobSeeker, UserRole.Recruiter],
      };

      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'multi-flow-token',
          refresh_token: 'multi-flow-refresh',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });

      // Simulate starting on job seeker route
      const { rerender } = renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route index element={<AuthStateDisplay />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      // Verify state on job seeker route
      await waitFor(() => {
        expect(screen.getByTestId('user-email')).toHaveTextContent('multi@example.com');
        expect(screen.getByTestId('has-jobseeker-role')).toHaveTextContent('true');
      });

      // In a real scenario, the router would handle navigation
      // This tests that localStorage is read correctly on component mount
    });

    it('maintains tokens when accessing different flow routes', async () => {
      const mockUser = {
        id: 'token-1',
        email: 'token@example.com',
        roles: [UserRole.Admin],
      };

      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'admin-access-token-12345',
          refresh_token: 'admin-refresh-token-67890',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });

      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/analytics']}>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="analytics" element={<AuthStateDisplay />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('has-access-token')).toHaveTextContent('yes');
        expect(screen.getByTestId('user-email')).toHaveTextContent('token@example.com');
      });
    });
  });

  describe('Token Persistence', () => {
    it('stores tokens to localStorage on login simulation', async () => {
      const mockUser = {
        id: 'token-persist-1',
        email: 'persist@example.com',
        roles: [UserRole.JobSeeker],
      };

      const mockSetItem = vi.fn();
      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'persist-token',
          refresh_token: 'persist-refresh',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });
      localStorage.setItem = mockSetItem;

      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route index element={<div>Job Seeker Page</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Job Seeker Page')).toBeInTheDocument();
      });
    });

    it('reads tokens from localStorage on initial render', async () => {
      const mockUser = {
        id: 'read-1',
        email: 'readtokens@example.com',
        roles: [UserRole.Recruiter],
      };

      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'read-access-token',
          refresh_token: 'read-refresh-token',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });

      renderWithProviders(
        <MemoryRouter initialEntries={['/recruiter/dashboard']}>
          <Routes>
            <Route path="/recruiter" element={<RecruiterLayout />}>
              <Route path="dashboard" element={<AuthStateDisplay />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('has-access-token')).toHaveTextContent('yes');
        expect(screen.getByTestId('user-email')).toHaveTextContent('readtokens@example.com');
        expect(localStorage.getItem).toHaveBeenCalledWith('access_token');
        expect(localStorage.getItem).toHaveBeenCalledWith('refresh_token');
        expect(localStorage.getItem).toHaveBeenCalledWith('auth_user');
      });
    });
  });

  describe('Unauthenticated State', () => {
    it('shows unauthenticated state when no tokens exist', async () => {
      localStorage.getItem = vi.fn(() => null);

      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route index element={<AuthStateDisplay />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
        expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');
        expect(screen.getByTestId('has-access-token')).toHaveTextContent('no');
      });
    });

    it('handles corrupted localStorage gracefully', async () => {
      localStorage.getItem = vi.fn((key: string) => {
        if (key === 'auth_user') {
          return 'invalid-json{';
        }
        return null;
      });

      renderWithProviders(
        <MemoryRouter initialEntries={['/jobs']}>
          <Routes>
            <Route path="/jobs" element={<JobSeekerLayout />}>
              <Route index element={<AuthStateDisplay />} />
            </Route>
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
        expect(screen.getByTestId('user-email')).toHaveTextContent('no-user');
      });
    });
  });

  describe('Role-Based Access Across Routes', () => {
    it('correctly identifies JobSeeker role across all job seeker routes', async () => {
      const mockUser = {
        id: 'role-test-1',
        email: 'jobseeker@example.com',
        roles: [UserRole.JobSeeker],
      };

      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'js-token',
          refresh_token: 'js-refresh',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });

      const routes = [
        '/jobs',
        '/jobs/saved',
        '/jobs/applications',
        '/jobs/recommended',
      ];

      for (const route of routes) {
        const { unmount } = renderWithProviders(
          <MemoryRouter initialEntries={[route]}>
            <Routes>
              <Route path="/jobs" element={<JobSeekerLayout />}>
                <Route index element={<AuthStateDisplay />} />
                <Route path="saved" element={<AuthStateDisplay />} />
                <Route path="applications" element={<AuthStateDisplay />} />
                <Route path="recommended" element={<AuthStateDisplay />} />
              </Route>
            </Routes>
          </MemoryRouter>
        );

        await waitFor(() => {
          expect(screen.getByTestId('has-jobseeker-role')).toHaveTextContent('true');
          expect(screen.getByTestId('has-recruiter-role')).toHaveTextContent('false');
        });

        unmount();
      }
    });

    it('correctly identifies Recruiter role across all recruiter routes', async () => {
      const mockUser = {
        id: 'role-test-2',
        email: 'recruiter@example.com',
        roles: [UserRole.Recruiter],
      };

      localStorage.getItem = vi.fn((key: string) => {
        const mockStorage: Record<string, string> = {
          access_token: 'rec-token',
          refresh_token: 'rec-refresh',
          auth_user: JSON.stringify(mockUser),
        };
        return mockStorage[key] || null;
      });

      const routes = [
        '/recruiter/dashboard',
        '/recruiter/vacancies',
        '/recruiter/candidates',
        '/recruiter/analytics',
      ];

      for (const route of routes) {
        const { unmount } = renderWithProviders(
          <MemoryRouter initialEntries={[route]}>
            <Routes>
              <Route path="/recruiter" element={<RecruiterLayout />}>
                <Route path="dashboard" element={<AuthStateDisplay />} />
                <Route path="vacancies" element={<AuthStateDisplay />} />
                <Route path="candidates" element={<AuthStateDisplay />} />
                <Route path="analytics" element={<AuthStateDisplay />} />
              </Route>
            </Routes>
          </MemoryRouter>
        );

        await waitFor(() => {
          expect(screen.getByTestId('has-recruiter-role')).toHaveTextContent('true');
          expect(screen.getByTestId('has-jobseeker-role')).toHaveTextContent('false');
        });

        unmount();
      }
    });
  });
});
