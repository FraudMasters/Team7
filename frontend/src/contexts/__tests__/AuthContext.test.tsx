/**
 * Unit tests for AuthContext
 *
 * Tests cover authentication state management, role checking functions,
 * login/logout functionality, and role extraction from JWT tokens.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import type { User } from 'oidc-client-ts';
import {
  AuthContextProvider,
  useAuthContext,
  extractUserRoles,
  withAuth,
  withRole,
  UserRole,
} from '../AuthContext';

// Mock react-oidc-context
vi.mock('react-oidc-context', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: vi.fn(),
}));

const mockSigninRedirect = vi.fn();
const mockSignoutRedirect = vi.fn();

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.location.origin
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { origin: 'http://localhost:5173' },
    });
  });

  describe('extractUserRoles', () => {
    it('should extract roles from user profile resource_access', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'testuser',
          email: 'test@example.com',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Admin', 'Recruiter'],
            },
          },
        },
        access_token: 'mock-token',
        token_type: 'Bearer',
        scope: 'openid profile email',
      } as User;

      const roles = extractUserRoles(mockUser);

      expect(roles).toEqual(['Admin', 'Recruiter']);
    });

    it('should return empty array when user is null', () => {
      const roles = extractUserRoles(null);
      expect(roles).toEqual([]);
    });

    it('should return empty array when resource_access is missing', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'testuser',
        },
        access_token: 'mock-token',
        token_type: 'Bearer',
      } as User;

      const roles = extractUserRoles(mockUser);

      expect(roles).toEqual([]);
    });

    it('should return empty array when client roles are missing', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'testuser',
          resource_access: {
            'other-client': {
              roles: ['Admin'],
            },
          },
        },
        access_token: 'mock-token',
        token_type: 'Bearer',
      } as User;

      const roles = extractUserRoles(mockUser);

      expect(roles).toEqual([]);
    });

    it('should filter out invalid roles', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'testuser',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Admin', 'InvalidRole', 'Recruiter', 'AnotherInvalidRole'],
            },
          },
        },
        access_token: 'mock-token',
        token_type: 'Bearer',
      } as User;

      const roles = extractUserRoles(mockUser);

      expect(roles).toEqual(['Admin', 'Recruiter']);
    });

    it('should handle malformed resource_access gracefully', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'testuser',
          resource_access: null as any,
        },
        access_token: 'mock-token',
        token_type: 'Bearer',
      } as User;

      const roles = extractUserRoles(mockUser);

      expect(roles).toEqual([]);
    });

    it('should return all three valid roles', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'testuser',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Admin', 'Recruiter', 'Viewer'],
            },
          },
        },
        access_token: 'mock-token',
        token_type: 'Bearer',
      } as User;

      const roles = extractUserRoles(mockUser);

      expect(roles).toEqual(['Admin', 'Recruiter', 'Viewer']);
    });
  });

  describe('useAuthContext', () => {
    it('should throw error when used outside AuthContextProvider', () => {
      // Suppress console.error for this test
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        renderHook(() => useAuthContext());
      }).toThrow('useAuthContext must be used within an AuthContextProvider');

      consoleErrorSpy.mockRestore();
    });

    it('should provide authentication state when within provider', () => {
      const { result } = renderHook(() => useAuthContext(), {
        wrapper: ({ children }) => (
          <AuthContextProvider>{children}</AuthContextProvider>
        ),
      });

      expect(result.current).toBeDefined();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.user).toBe(null);
      expect(result.current.roles).toEqual([]);
    });

    it('should have login and logout functions', () => {
      const { result } = renderHook(() => useAuthContext(), {
        wrapper: ({ children }) => (
          <AuthContextProvider>{children}</AuthContextProvider>
        ),
      });

      expect(typeof result.current.login).toBe('function');
      expect(typeof result.current.logout).toBe('function');
    });

    it('should have role checking functions', () => {
      const { result } = renderHook(() => useAuthContext(), {
        wrapper: ({ children }) => (
          <AuthContextProvider>{children}</AuthContextProvider>
        ),
      });

      expect(typeof result.current.hasRole).toBe('function');
      expect(typeof result.current.hasAnyRole).toBe('function');
      expect(typeof result.current.hasAllRoles).toBe('function');
    });
  });

  describe('hasRole', () => {
    it('should return true when user has the role', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'admin',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Admin'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        // Mock useOidcAuth to return our mock user
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.hasRole('Admin')).toBe(true);
    });

    it('should return false when user does not have the role', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'viewer',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Viewer'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.hasRole('Admin')).toBe(false);
    });

    it('should return false when user has no roles', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'noroles',
          resource_access: {
            'agenthr-frontend': {
              roles: [],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.hasRole('Admin')).toBe(false);
      expect(result.current.hasRole('Recruiter')).toBe(false);
      expect(result.current.hasRole('Viewer')).toBe(false);
    });
  });

  describe('hasAnyRole', () => {
    it('should return true when user has at least one of the required roles', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'recruiter',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Recruiter'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.hasAnyRole(['Admin', 'Recruiter'])).toBe(true);
    });

    it('should return true when user has multiple matching roles', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'superuser',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Admin', 'Recruiter', 'Viewer'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.hasAnyRole(['Admin', 'Recruiter'])).toBe(true);
    });

    it('should return false when user has none of the required roles', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'viewer',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Viewer'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.hasAnyRole(['Admin', 'Recruiter'])).toBe(false);
    });
  });

  describe('hasAllRoles', () => {
    it('should return true when user has all required roles', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'superuser',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Admin', 'Recruiter', 'Viewer'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.hasAllRoles(['Admin', 'Recruiter'])).toBe(true);
    });

    it('should return false when user is missing one required role', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'recruiter',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Recruiter'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.hasAllRoles(['Admin', 'Recruiter'])).toBe(false);
    });

    it('should return true when checking single role that user has', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'admin',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Admin'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.hasAllRoles(['Admin'])).toBe(true);
    });
  });

  describe('login and logout', () => {
    it('should call signinRedirect when login is called', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'testuser',
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      act(() => {
        result.current.login();
      });

      expect(mockSigninRedirect).toHaveBeenCalledTimes(1);
    });

    it('should call signoutRedirect when logout is called', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'testuser',
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      act(() => {
        result.current.logout();
      });

      expect(mockSignoutRedirect).toHaveBeenCalledTimes(1);
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when user is logged in', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'testuser',
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should return false when user is not logged in', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: null,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const { result } = renderHook(() => useAuthContext(), {
        wrapper,
      });

      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('withAuth HOC', () => {
    it('should render component when authenticated', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'testuser',
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const TestComponent = ({ user }: { user: User | null }) => (
        <div>Welcome {user?.profile.preferred_username}</div>
      );

      const ProtectedComponent = withAuth(TestComponent);

      const { getByText } = render(
        <AuthContextProvider>
          <ProtectedComponent />
        </AuthContextProvider>
      );

      expect(getByText('Welcome testuser')).toBeInTheDocument();
    });

    it('should render login message when not authenticated', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: null,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const TestComponent = ({ user }: { user: User | null }) => (
        <div>Welcome {user?.profile.preferred_username}</div>
      );

      const ProtectedComponent = withAuth(TestComponent);

      const { getByText } = render(
        <AuthContextProvider>
          <ProtectedComponent />
        </AuthContextProvider>
      );

      expect(getByText('Please log in to access this feature.')).toBeInTheDocument();
    });

    it('should render loading when loading', () => {
      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: null,
          isLoading: true,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const TestComponent = ({ user }: { user: User | null }) => (
        <div>Welcome {user?.profile.preferred_username}</div>
      );

      const ProtectedComponent = withAuth(TestComponent);

      const { getByText } = render(
        <AuthContextProvider>
          <ProtectedComponent />
        </AuthContextProvider>
      );

      expect(getByText('Loading...')).toBeInTheDocument();
    });
  });

  describe('withRole HOC', () => {
    it('should render component when user has required role', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'admin',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Admin'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const TestComponent = () => <div>Admin Panel</div>;
      const AdminComponent = withRole('Admin')(TestComponent);

      const { getByText } = render(
        <AuthContextProvider>
          <AdminComponent />
        </AuthContextProvider>
      );

      expect(getByText('Admin Panel')).toBeInTheDocument();
    });

    it('should render access denied when user lacks required role', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'viewer',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Viewer'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const TestComponent = () => <div>Admin Panel</div>;
      const AdminComponent = withRole('Admin')(TestComponent);

      const { getByText } = render(
        <AuthContextProvider>
          <AdminComponent />
        </AuthContextProvider>
      );

      expect(getByText('You do not have permission to access this feature.')).toBeInTheDocument();
    });

    it('should render component when user has any of the required roles', () => {
      const mockUser: User = {
        profile: {
          sub: 'user123',
          preferred_username: 'recruiter',
          resource_access: {
            'agenthr-frontend': {
              roles: ['Recruiter'],
            },
          },
        },
        access_token: 'token',
        token_type: 'Bearer',
      } as User;

      const wrapper = ({ children }: { children: React.ReactNode }) => {
        const { AuthProvider } = require('react-oidc-context');
        const useOidcAuth = require('react-oidc-context').useAuth;
        (useOidcAuth as any).mockReturnValue({
          user: mockUser,
          isLoading: false,
          error: undefined,
          signinRedirect: mockSigninRedirect,
          signoutRedirect: mockSignoutRedirect,
        });

        return <AuthProvider>{children}</AuthProvider>;
      };

      const TestComponent = () => <div>Management Panel</div>;
      const ManagementComponent = withRole(['Admin', 'Recruiter'])(TestComponent);

      const { getByText } = render(
        <AuthContextProvider>
          <ManagementComponent />
        </AuthContextProvider>
      );

      expect(getByText('Management Panel')).toBeInTheDocument();
    });
  });
});
