/**
 * Unit tests for ProtectedRoute component
 *
 * Tests cover authentication checks, role-based access control,
 * redirect behavior, loading states, and access denied messages.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MemoryRouter, Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import ProtectedRoute from '../ProtectedRoute';

// Mock useAuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuthContext: vi.fn(),
}));

const { useAuthContext } = require('@/contexts/AuthContext');

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const TestComponent = () => <div>Protected Content</div>;

  describe('Authentication Check', () => {
    it('should render children when user is authenticated', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn(() => true),
        hasAnyRole: vi.fn(() => true),
        user: { profile: { preferred_username: 'testuser' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should redirect to login when user is not authenticated', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: null,
      });

      const history = createMemoryHistory();
      history.push('/protected');

      render(
        <Router location={history.location} navigator={history}>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </Router>
      );

      // Should redirect to /login
      expect(history.location.pathname).toBe('/login');
    });

    it('should preserve location state for redirect after login', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: null,
      });

      const history = createMemoryHistory();
      history.push('/protected-page');

      render(
        <Router location={history.location} navigator={history}>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </Router>
      );

      expect(history.location.state).toBeDefined();
      expect(history.location.state.from.pathname).toBe('/protected-page');
    });

    it('should show loading state while checking authentication', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: null,
      });

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Checking authentication...')).toBeInTheDocument();
    });
  });

  describe('Role-Based Access Control', () => {
    it('should render children when user has required single role', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn((role: string) => role === 'Admin'),
        hasAnyRole: vi.fn(() => true),
        user: { profile: { preferred_username: 'admin' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles="Admin">
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should render children when user has one of multiple required roles', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn((role: string) => role === 'Recruiter'),
        hasAnyRole: vi.fn((roles: string[]) => roles.includes('Recruiter')),
        user: { profile: { preferred_username: 'recruiter' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles={['Admin', 'Recruiter']}>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should show access denied when user lacks required single role', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: { profile: { preferred_username: 'viewer' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles="Admin">
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.getByText(/You do not have permission to access this page/)).toBeInTheDocument();
      expect(screen.getByText(/Required roles: Admin/)).toBeInTheDocument();
    });

    it('should show access denied when user lacks any of the required roles', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: { profile: { preferred_username: 'viewer' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles={['Admin', 'Recruiter']}>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.getByText(/Required roles: Admin, Recruiter/)).toBeInTheDocument();
    });

    it('should render children when no role requirements specified', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: { profile: { preferred_username: 'user' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  describe('Custom Redirect Paths', () => {
    it('should redirect to custom login path when specified', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: null,
      });

      const history = createMemoryHistory();

      render(
        <Router location={history.location} navigator={history}>
          <ProtectedRoute redirectTo="/custom-login">
            <TestComponent />
          </ProtectedRoute>
        </Router>
      );

      expect(history.location.pathname).toBe('/custom-login');
    });
  });

  describe('Loading State', () => {
    it('should show CircularProgress while loading', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: null,
      });

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      // Check for CircularProgress (renders as a div with role="progressbar")
      const progressElement = document.querySelector('[role="progressbar"]');
      expect(progressElement).toBeInTheDocument();
    });

    it('should show loading message while checking authentication', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: null,
      });

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Checking authentication...')).toBeInTheDocument();
    });

    it('should not render children while loading', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: null,
      });

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Access Denied Display', () => {
    it('should display proper access denied message', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: { profile: { preferred_username: 'viewer' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles="Admin">
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
      expect(screen.getByText('You do not have permission to access this page.')).toBeInTheDocument();
    });

    it('should display required role for single role requirement', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: { profile: { preferred_username: 'viewer' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles="Admin">
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText(/Required roles: Admin/)).toBeInTheDocument();
    });

    it('should display all required roles for multiple role requirement', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: { profile: { preferred_username: 'viewer' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles={['Admin', 'Recruiter', 'SuperUser']}>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText(/Required roles: Admin, Recruiter, SuperUser/)).toBeInTheDocument();
    });

    it('should not render children when access denied', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: { profile: { preferred_username: 'viewer' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles="Admin">
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    });
  });

  describe('Integration Scenarios', () => {
    it('should allow Admin to access admin-only route', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn((role: string) => role === 'Admin'),
        hasAnyRole: vi.fn((roles: string[]) => roles.includes('Admin')),
        user: { profile: { preferred_username: 'admin' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles="Admin">
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should deny Recruiter access to admin-only route', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn((role: string) => role === 'Recruiter'),
        hasAnyRole: vi.fn((roles: string[]) => roles.includes('Recruiter')),
        user: { profile: { preferred_username: 'recruiter' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles="Admin">
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
    });

    it('should allow Recruiter to access recruiter endpoints', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn((role: string) => role === 'Recruiter'),
        hasAnyRole: vi.fn((roles: string[]) => roles.includes('Recruiter') || roles.includes('Admin')),
        user: { profile: { preferred_username: 'recruiter' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles={['Admin', 'Recruiter']}>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should allow Viewer to access public authenticated endpoints', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn((role: string) => role === 'Viewer'),
        hasAnyRole: vi.fn(() => false),
        user: { profile: { preferred_username: 'viewer' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });

    it('should deny Viewer access to write endpoints', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        hasRole: vi.fn((role: string) => role === 'Viewer'),
        hasAnyRole: vi.fn((roles: string[]) => roles.includes('Viewer')),
        user: { profile: { preferred_username: 'viewer' } },
      });

      render(
        <MemoryRouter>
          <ProtectedRoute requiredRoles={['Admin', 'Recruiter']}>
            <TestComponent />
          </ProtectedRoute>
        </MemoryRouter>
      );

      expect(screen.getByText('Access Denied')).toBeInTheDocument();
    });

    it('should redirect unauthenticated user to login from protected route', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        hasRole: vi.fn(() => false),
        hasAnyRole: vi.fn(() => false),
        user: null,
      });

      const history = createMemoryHistory();
      history.push('/dashboard');

      render(
        <Router location={history.location} navigator={history}>
          <ProtectedRoute>
            <TestComponent />
          </ProtectedRoute>
        </Router>
      );

      expect(history.location.pathname).toBe('/login');
      expect(history.location.state.from.pathname).toBe('/dashboard');
    });
  });
});
