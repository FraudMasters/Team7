/**
 * Tests for ProtectedRoute Component
 *
 * Tests the route protection component including:
 * - Auth bypass mode when AUTH_ENABLED is false
 * - Role-based access control
 * - Redirect behavior for unauthorized users
 * - Loading and access denied states
 * - Feature flag integration
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter, Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import ProtectedRoute, { ProtectedRouteProps, UserRole } from './ProtectedRoute';

// Mock the feature flags
vi.mock('@/config/features', () => ({
  FEATURE_FLAGS: {
    AUTH_ENABLED: false,
    AUTH_DEBUG: false,
    MOCK_ROLE: 'Admin',
    ROUTE_PROTECTION_ENABLED: true,
  },
  getFeatureFlag: vi.fn((flag: string) => {
    switch (flag) {
      case 'MOCK_ROLE':
        return 'Admin';
      case 'AUTH_ENABLED':
        return false;
      default:
        return undefined;
    }
  }),
}));

// Import after mocking
import { FEATURE_FLAGS, getFeatureFlag } from '@/config/features';

describe('ProtectedRoute', () => {
  const mockChildren = <div>Protected Content</div>;
  const defaultProps: ProtectedRouteProps = {
    children: mockChildren,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    // Reset to default: auth disabled
    (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
    vi.mocked(getFeatureFlag).mockImplementation((flag: string) => {
      switch (flag) {
        case 'MOCK_ROLE':
          return 'Admin';
        default:
          return undefined;
      }
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Auth Bypass Mode (AUTH_ENABLED=false)', () => {
    beforeEach(() => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
    });

    it('should render children when auth is disabled', () => {
      render(
        <MemoryRouter>
          <ProtectedRoute {...defaultProps} />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should bypass role checks when auth is disabled', () => {
      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Admin']}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should bypass role checks for any role requirement when auth is disabled', () => {
      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Recruiter', 'Admin']}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should bypass role checks for JobSeeker role when auth is disabled', () => {
      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['JobSeeker']}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should work without any role requirements when auth is disabled', () => {
      render(
        <MemoryRouter>
          <ProtectedRoute {...defaultProps} />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  describe('Auth Enabled Mode (AUTH_ENABLED=true)', () => {
    beforeEach(() => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
    });

    it('should render children when user has required role', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('Admin');

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Admin']}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should render children when user has one of multiple required roles', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('Recruiter');

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Recruiter', 'Admin']}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should show access denied when user does not have required role', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Admin']}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
    });

    it('should show access denied when user role is not in required roles list', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Recruiter', 'Admin']}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
    });

    it('should render children when no role requirements specified', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <MemoryRouter>
          <ProtectedRoute {...defaultProps} />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should show custom access denied fallback when provided', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');
      const customFallback = <div>Custom Access Denied Message</div>;

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Admin']}
            accessDeniedFallback={customFallback}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Custom Access Denied Message')).toBeInTheDocument();
      expect(screen.queryByText('Access Denied')).not.toBeInTheDocument();
    });

    it('should display redirect path in default access denied message', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Admin']}
            redirectTo="/login"
          />
        </MemoryRouter>
      );

      expect(screen.getByText('/login')).toBeInTheDocument();
    });
  });

  describe('Role Validation', () => {
    beforeEach(() => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
    });

    describe('Admin Role', () => {
      it('should grant access to Admin-only routes', () => {
        vi.mocked(getFeatureFlag).mockReturnValue('Admin');

        render(
          <MemoryRouter>
            <ProtectedRoute
              {...defaultProps}
              requiredRoles={['Admin']}
            />
          </MemoryRouter>
        );

        expect(screen.getByText('Protected Content')).toBeInTheDocument();
      });

      it('should grant access to Admin+Recruiter routes', () => {
        vi.mocked(getFeatureFlag).mockReturnValue('Admin');

        render(
          <MemoryRouter>
            <ProtectedRoute
              {...defaultProps}
              requiredRoles={['Recruiter', 'Admin']}
            />
          </MemoryRouter>
        );

        expect(screen.getByText('Protected Content')).toBeInTheDocument();
      });
    });

    describe('Recruiter Role', () => {
      it('should grant access to Recruiter-only routes', () => {
        vi.mocked(getFeatureFlag).mockReturnValue('Recruiter');

        render(
          <MemoryRouter>
            <ProtectedRoute
              {...defaultProps}
              requiredRoles={['Recruiter']}
            />
          </MemoryRouter>
        );

        expect(screen.getByText('Protected Content')).toBeInTheDocument();
      });

      it('should deny access to Admin-only routes', () => {
        vi.mocked(getFeatureFlag).mockReturnValue('Recruiter');

        render(
          <MemoryRouter>
            <ProtectedRoute
              {...defaultProps}
              requiredRoles={['Admin']}
            />
          </MemoryRouter>
        );

        expect(screen.getByText('Access Denied')).toBeInTheDocument();
      });
    });

    describe('JobSeeker Role', () => {
      it('should grant access to JobSeeker-only routes', () => {
        vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

        render(
          <MemoryRouter>
            <ProtectedRoute
              {...defaultProps}
              requiredRoles={['JobSeeker']}
            />
          </MemoryRouter>
        );

        expect(screen.getByText('Protected Content')).toBeInTheDocument();
      });

      it('should deny access to Recruiter routes', () => {
        vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

        render(
          <MemoryRouter>
            <ProtectedRoute
              {...defaultProps}
              requiredRoles={['Recruiter']}
            />
          </MemoryRouter>
        );

        expect(screen.getByText('Access Denied')).toBeInTheDocument();
      });

      it('should deny access to Admin routes', () => {
        vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

        render(
          <MemoryRouter>
            <ProtectedRoute
              {...defaultProps}
              requiredRoles={['Admin']}
            />
          </MemoryRouter>
        );

        expect(screen.getByText('Access Denied')).toBeInTheDocument();
      });
    });
  });

  describe('Debug Mode', () => {
    it('should enable debug logging when AUTH_DEBUG is true', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
      (FEATURE_FLAGS.AUTH_DEBUG as boolean) = true;

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

      render(
        <MemoryRouter>
          <ProtectedRoute {...defaultProps} />
        </MemoryRouter>
      );

      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });

  describe('Component Structure', () => {
    it('should export UserRole type', () => {
      const role: UserRole = 'Admin';
      expect(role).toBe('Admin');
    });

    it('should accept all valid UserRole values', () => {
      const roles: UserRole[] = ['JobSeeker', 'Recruiter', 'Admin'];
      expect(roles).toHaveLength(3);
    });

    it('should render multiple children', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <div>First Child</div>
            <div>Second Child</div>
            <div>Third Child</div>
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('First Child')).toBeInTheDocument();
      expect(screen.getByText('Second Child')).toBeInTheDocument();
      expect(screen.getByText('Third Child')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty requiredRoles array', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={[]}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should handle undefined redirectTo', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Admin']}
            redirectTo={undefined}
          />
        </MemoryRouter>
      );

      // Should show access denied with default redirect '/'
      expect(screen.getByText('Access Denied')).toBeInTheDocument();
    });

    it('should handle all three roles in requiredRoles', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['JobSeeker', 'Recruiter', 'Admin']}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  describe('Integration with React Router', () => {
    it('should work within MemoryRouter', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <ProtectedRoute {...defaultProps} />
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should preserve router context', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;

      const history = createMemoryHistory({ initialEntries: ['/protected'] });

      render(
        <Router location={history.location} navigator={history}>
          <ProtectedRoute {...defaultProps} />
        </Router>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  describe('Default Redirect', () => {
    it('should use "/" as default redirect path', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Admin']}
          />
        </MemoryRouter>
      );

      expect(screen.getByText('/')).toBeInTheDocument();
    });

    it('should use custom redirect path when provided', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <MemoryRouter>
          <ProtectedRoute
            {...defaultProps}
            requiredRoles={['Admin']}
            redirectTo="/custom-login"
          />
        </MemoryRouter>
      );

      expect(screen.getByText('/custom-login')).toBeInTheDocument();
    });
  });
});
