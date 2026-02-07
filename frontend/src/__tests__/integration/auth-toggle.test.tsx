/**
 * Integration Tests: Auth Toggle Functionality Verification
 *
 * Tests the auth toggle feature that allows enabling/disabling authentication
 * via the VITE_AUTH_ENABLED environment variable.
 *
 * Verification Steps (from spec - subtask-7-4):
 * 1. Set VITE_AUTH_ENABLED=false
 * 2. Restart frontend
 * 3. Access protected routes without login
 * 4. Set VITE_AUTH_ENABLED=true
 * 5. Restart frontend
 * 6. Verify auth required for protected routes
 *
 * This test suite verifies:
 * - Auth bypass behavior when AUTH_ENABLED=false
 * - Auth enforcement when AUTH_ENABLED=true
 * - Role-based access control in both modes
 * - Protected route behavior with different roles
 * - Feature flag integration
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import userEvent from '@testing-library/user-event';

// Components to test
import ProtectedRoute from '../../components/ProtectedRoute';
import { AdminDashboard } from '../../pages/admin/AdminDashboard';
import { AdminUsers } from '../../pages/admin/AdminUsers';
import { AdminSettings } from '../../pages/admin/AdminSettings';
import AdminLayout from '../../layouts/AdminLayout';
import AdminAuditLogsPage from '../../pages/admin/AdminAuditLogs';

// Context Providers
import { ThemeProvider } from '../../contexts/ThemeContext';
import { LanguageProvider } from '../../contexts/LanguageContext';

// Feature flags
import { FEATURE_FLAGS, getFeatureFlag } from '../../config/features';
import type { UserRole } from '../../components/ProtectedRoute';

/**
 * Test wrapper with providers
 */
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>
        <LanguageProvider>
          {children}
        </LanguageProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

describe('Auth Toggle Functionality - Integration Tests', () => {
  const mockChildren = <div data-testid="protected-content">Protected Content</div>;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Phase 1: Auth Disabled Mode (VITE_AUTH_ENABLED=false)', () => {
    beforeEach(() => {
      // Simulate VITE_AUTH_ENABLED=false
      vi.stubGlobal('import', {
        meta: {
          env: {
            VITE_AUTH_ENABLED: 'false',
            VITE_MOCK_ROLE: 'Admin',
          },
        },
      });
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
      vi.mocked(getFeatureFlag).mockImplementation((flag: string) => {
        switch (flag) {
          case 'MOCK_ROLE':
            return 'Admin';
          case 'AUTH_ENABLED':
            return false;
          default:
            return undefined;
        }
      });
    });

    /**
     * Step 1-3: Verify auth bypass mode works correctly
     */
    it('should bypass all auth checks when VITE_AUTH_ENABLED=false', () => {
      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should access Admin routes without authentication when auth disabled', async () => {
      render(
        <TestWrapper>
          <Routes>
            <Route
              path="/admin/dashboard"
              element={
                <ProtectedRoute requiredRoles={['Admin']}>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
          </Routes>
        </TestWrapper>
      );

      // Should render AdminDashboard content without auth check
      await waitFor(() => {
        expect(screen.getByText(/System Overview/i)).toBeInTheDocument();
      });
    });

    it('should access Admin Users route without authentication when auth disabled', async () => {
      render(
        <TestWrapper>
          <Routes>
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute requiredRoles={['Admin']}>
                  <AdminUsers />
                </ProtectedRoute>
              }
            />
          </Routes>
        </TestWrapper>
      );

      // Should render AdminUsers content without auth check
      await waitFor(() => {
        expect(screen.getByText(/User Management/i)).toBeInTheDocument();
      });
    });

    it('should access Admin Settings route without authentication when auth disabled', async () => {
      render(
        <TestWrapper>
          <Routes>
            <Route
              path="/admin/settings"
              element={
                <ProtectedRoute requiredRoles={['Admin']}>
                  <AdminSettings />
                </ProtectedRoute>
              }
            />
          </Routes>
        </TestWrapper>
      );

      // Should render AdminSettings content without auth check
      await waitFor(() => {
        expect(screen.getByText(/System Configuration/i)).toBeInTheDocument();
      });
    });

    it('should access Admin Audit Logs route without authentication when auth disabled', async () => {
      render(
        <TestWrapper>
          <Routes>
            <Route
              path="/admin/audit-logs"
              element={
                <ProtectedRoute requiredRoles={['Admin']}>
                  <AdminAuditLogsPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </TestWrapper>
      );

      // Should render AdminAuditLogsPage content without auth check
      await waitFor(() => {
        expect(screen.getByText(/Audit Logs/i)).toBeInTheDocument();
      });
    });

    it('should bypass role checks for any role when auth disabled', () => {
      const testRoles: UserRole[][] = [
        ['Admin'],
        ['Recruiter'],
        ['JobSeeker'],
        ['Recruiter', 'Admin'],
        ['JobSeeker', 'Recruiter', 'Admin'],
      ];

      testRoles.forEach((roles) => {
        const { unmount } = render(
          <TestWrapper>
            <ProtectedRoute requiredRoles={roles}>
              <div data-testid={`content-${roles.join('-')}`}>
                Content for {roles.join(', ')}
              </div>
            </ProtectedRoute>
          </TestWrapper>
        );

        expect(screen.getByTestId(`content-${roles.join('-')}`)).toBeInTheDocument();
        unmount();
      });
    });

    it('should work with no role requirements when auth disabled', () => {
      render(
        <TestWrapper>
          <ProtectedRoute>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Phase 2: Auth Enabled Mode (VITE_AUTH_ENABLED=true)', () => {
    beforeEach(() => {
      // Simulate VITE_AUTH_ENABLED=true
      vi.stubGlobal('import', {
        meta: {
          env: {
            VITE_AUTH_ENABLED: 'true',
            VITE_MOCK_ROLE: 'Admin',
          },
        },
      });
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
    });

    /**
     * Step 4-6: Verify auth enforcement works correctly
     */
    it('should enforce role checks when VITE_AUTH_ENABLED=true with Admin role', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('Admin');

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should enforce role checks when VITE_AUTH_ENABLED=true with Recruiter role', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('Recruiter');

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Recruiter', 'Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should enforce role checks when VITE_AUTH_ENABLED=true with JobSeeker role', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['JobSeeker']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should deny access when user does not have required role (Admin-only route)', async () => {
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      // Should show access denied message
      await waitFor(() => {
        expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
      });

      // Protected content should not be visible
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('should deny access when user does not have any of the required roles', async () => {
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Recruiter', 'Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      // Should show access denied message
      await waitFor(() => {
        expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
      });

      // Protected content should not be visible
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    });

    it('should allow access when user has at least one of the required roles', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('Recruiter');

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Recruiter', 'Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should allow Admin role to access any protected route', () => {
      vi.mocked(getFeatureFlag).mockReturnValue('Admin');

      const roleCombinations: UserRole[][] = [
        ['Admin'],
        ['Recruiter'],
        ['JobSeeker'],
        ['Recruiter', 'Admin'],
        ['JobSeeker', 'Recruiter'],
      ];

      roleCombinations.forEach((roles) => {
        const { unmount } = render(
          <TestWrapper>
            <ProtectedRoute requiredRoles={roles}>
              <div data-testid={`admin-access-${roles.join('-')}`}>
                Admin accessing {roles.join(', ')}
              </div>
            </ProtectedRoute>
          </TestWrapper>
        );

        // Admin should have access to all routes
        expect(screen.getByTestId(`admin-access-${roles.join('-')}`)).toBeInTheDocument();
        unmount();
      });
    });

    it('should show access denied for non-matching roles', async () => {
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']} redirectTo="/">
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      // Should show access denied message
      await waitFor(() => {
        expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
        expect(screen.getByText(/don't have permission/i)).toBeInTheDocument();
      });

      // Should mention redirect
      expect(screen.getByText(/Redirecting to/i)).toBeInTheDocument();
      expect(screen.getByText(/\//)).toBeInTheDocument();
    });
  });

  describe('Auth Toggle State Transitions', () => {
    /**
     * Verify toggle behavior between states
     */
    it('should transition from disabled to enabled correctly', async () => {
      // Start with auth disabled
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
      vi.mocked(getFeatureFlag).mockReturnValue('Admin');

      const { rerender } = render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      // Should render content when disabled
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();

      // Simulate enabling auth (VITE_AUTH_ENABLED=true)
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;

      rerender(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      // Should still render content (Admin role matches)
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });

    it('should transition from enabled to disabled correctly', async () => {
      // Start with auth enabled
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
      vi.mocked(getFeatureFlag).mockReturnValue('JobSeeker');

      const { rerender } = render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      // Should deny access (JobSeeker doesn't have Admin role)
      await waitFor(() => {
        expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
      });

      // Simulate disabling auth (VITE_AUTH_ENABLED=false)
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;

      rerender(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      // Should now render content (auth bypassed)
      expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    });
  });

  describe('Feature Flag Integration', () => {
    it('should respect FEATURE_FLAGS.AUTH_ENABLED value', () => {
      // Test with AUTH_ENABLED=false
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;

      const { unmount: unmount1 } = render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']}>
            <div data-testid="auth-disabled-test">Auth Disabled</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByTestId('auth-disabled-test')).toBeInTheDocument();
      unmount1();

      // Test with AUTH_ENABLED=true
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;
      vi.mocked(getFeatureFlag).mockReturnValue('Admin');

      const { unmount: unmount2 } = render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']}>
            <div data-testid="auth-enabled-test">Auth Enabled</div>
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(screen.getByTestId('auth-enabled-test')).toBeInTheDocument();
      unmount2();
    });

    it('should use getFeatureFlag for mock role in auth enabled mode', () => {
      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = true;

      // Test with different mock roles
      const mockRoles: UserRole[] = ['Admin', 'Recruiter', 'JobSeeker'];

      mockRoles.forEach((role) => {
        vi.mocked(getFeatureFlag).mockReturnValue(role);

        const { unmount } = render(
          <TestWrapper>
            <ProtectedRoute requiredRoles={[role]}>
              <div data-testid={`mock-role-${role}`}>
                Mock Role: {role}
              </div>
            </ProtectedRoute>
          </TestWrapper>
        );

        expect(screen.getByTestId(`mock-role-${role}`)).toBeInTheDocument();
        unmount();
      });
    });
  });

  describe('Debug Mode Logging', () => {
    it('should log debug messages when VITE_AUTH_DEBUG=true', () => {
      const consoleGroupSpy = vi.spyOn(console, 'group').mockImplementation(() => {});
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const consoleGroupEndSpy = vi.spyOn(console, 'groupEnd').mockImplementation(() => {});

      (FEATURE_FLAGS.AUTH_ENABLED as boolean) = false;
      (FEATURE_FLAGS.AUTH_DEBUG as boolean) = true;

      render(
        <TestWrapper>
          <ProtectedRoute requiredRoles={['Admin']}>
            {mockChildren}
          </ProtectedRoute>
        </TestWrapper>
      );

      expect(consoleGroupSpy).toHaveBeenCalled();
      expect(consoleGroupEndSpy).toHaveBeenCalled();

      consoleGroupSpy.mockRestore();
      consoleLogSpy.mockRestore();
      consoleGroupEndSpy.mockRestore();
    });
  });
});
