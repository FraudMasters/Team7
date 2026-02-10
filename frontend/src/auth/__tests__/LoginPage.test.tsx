/**
 * Unit tests for LoginPage component
 *
 * Tests cover login form rendering, authentication flow,
 * redirect behavior, loading states, and error handling.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { MemoryRouter, Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import LoginPage from '../LoginPage';

// Mock useAuth from react-oidc-context
vi.mock('react-oidc-context', () => ({
  useAuth: vi.fn(),
}));

const { useAuth } = require('react-oidc-context');

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render login form correctly', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Welcome Back')).toBeInTheDocument();
      expect(screen.getByText(/Sign in to access the AgentHR platform/)).toBeInTheDocument();
    });

    it('should render login button', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const loginButton = screen.getByRole('button', { name: /sign in/i });
      expect(loginButton).toBeInTheDocument();
    });

    it('should render email and password input fields (disabled for Keycloak)', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      // Note: These fields are visual/disabled since actual auth happens via Keycloak
      const emailInput = screen.getByPlaceholderText(/email/i);
      const passwordInput = screen.getByPlaceholderText(/password/i);
      expect(emailInput).toBeInTheDocument();
      expect(passwordInput).toBeInTheDocument();
      expect(emailInput).toBeDisabled();
      expect(passwordInput).toBeDisabled();
    });

    it('should render "Forgot Password" link', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Forgot password?')).toBeInTheDocument();
    });

    it('should render link to registration page', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const registerLink = screen.getByText(/don't have an account/i);
      expect(registerLink).toBeInTheDocument();
      expect(screen.getByText('Create one')).toBeInTheDocument();
    });

    it('should display info alert about Keycloak redirect', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText(/You'll be redirected to Keycloak/)).toBeInTheDocument();
    });
  });

  describe('Login Flow', () => {
    it('should call signinRedirect when login button is clicked', async () => {
      const mockSigninRedirect = vi.fn();
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: mockSigninRedirect,
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const loginButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(loginButton);

      expect(mockSigninRedirect).toHaveBeenCalledTimes(1);
    });

    it('should trigger redirect to Keycloak on login', () => {
      const mockSigninRedirect = vi.fn();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: mockSigninRedirect,
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const loginButton = screen.getByRole('button', { name: /sign in/i });
      loginButton.click();

      expect(mockSigninRedirect).toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('should show loading state during authentication', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: true,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      // Check for CircularProgress (renders as a div with role="progressbar")
      const progressElement = document.querySelector('[role="progressbar"]');
      expect(progressElement).toBeInTheDocument();
    });

    it('should show "Signing in..." text while loading', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: true,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Signing in...')).toBeInTheDocument();
    });

    it('should disable login button while loading', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: true,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const loginButton = screen.getByRole('button', { name: /sign in/i });
      expect(loginButton).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('should display error message when authentication fails', () => {
      const mockError = new Error('Authentication failed');

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: mockError,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText(/authentication failed/i)).toBeInTheDocument();
    });
  });

  describe('Redirect Behavior', () => {
    it('should redirect authenticated users to home page', async () => {
      const history = createMemoryHistory();
      history.push('/login');

      useAuth.mockReturnValue({
        user: { profile: { sub: '123' } },
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <Router location={history.location} navigator={history}>
          <LoginPage />
        </Router>
      );

      await waitFor(() => {
        expect(history.location.pathname).toBe('/');
      });
    });

    it('should redirect authenticated users to original destination', async () => {
      const history = createMemoryHistory();
      history.push('/login');
      const from = { pathname: '/dashboard' };

      useAuth.mockReturnValue({
        user: { profile: { sub: '123' } },
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <Router
          location={history.location}
          navigator={history}
          state={{ from }}
        >
          <LoginPage />
        </Router>
      );

      await waitFor(() => {
        expect(history.location.pathname).toBe('/dashboard');
      });
    });

    it('should not redirect unauthenticated users', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      const history = createMemoryHistory();
      history.push('/login');

      render(
        <Router location={history.location} navigator={history}>
          <LoginPage />
        </Router>
      );

      expect(history.location.pathname).toBe('/login');
    });

    it('should not redirect while loading', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: true,
        error: null,
        signinRedirect: vi.fn(),
      });

      const history = createMemoryHistory();
      history.push('/login');

      render(
        <Router location={history.location} navigator={history}>
          <LoginPage />
        </Router>
      );

      expect(history.location.pathname).toBe('/login');
    });
  });

  describe('Navigation', () => {
    it('should navigate to registration page when create one link is clicked', async () => {
      const user = userEvent.setup();
      const history = createMemoryHistory();
      history.push('/login');

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <Router location={history.location} navigator={history}>
          <LoginPage />
        </Router>
      );

      const createOneLink = screen.getByText('Create one');
      await user.click(createOneLink);

      expect(history.location.pathname).toBe('/auth/register');
    });

    it('should preserve location state when navigating to register', async () => {
      const user = userEvent.setup();
      const history = createMemoryHistory();
      history.push('/login');
      const fromLocation = { pathname: '/protected-page', state: { from: '/dashboard' } };

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <Router
          location={history.location}
          navigator={history}
          state={fromLocation}
        >
          <LoginPage />
        </Router>
      );

      const createOneLink = screen.getByText('Create one');
      await user.click(createOneLink);

      expect(history.location.state).toBeDefined();
    });
  });

  describe('Visual Design', () => {
    it('should render login form in a Paper component', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      // Check for the Paper component by looking for its container
      const container = document.querySelector('.MuiPaper-root');
      expect(container).toBeInTheDocument();
    });

    it('should display email and password icons', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      // Icons should be present (rendered as SVG)
      const icons = document.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(0);
    });
  });

  describe('Integration with OIDC Auth', () => {
    it('should use signinRedirect from useAuth', () => {
      const mockSigninRedirect = vi.fn();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: mockSigninRedirect,
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const loginButton = screen.getByRole('button', { name: /sign in/i });
      loginButton.click();

      expect(mockSigninRedirect).toHaveBeenCalledTimes(1);
    });

    it('should access user state from useAuth', () => {
      useAuth.mockReturnValue({
        user: { profile: { sub: '123', email: 'test@example.com' } },
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      const history = createMemoryHistory();
      history.push('/login');

      render(
        <Router location={history.location} navigator={history}>
          <LoginPage />
        </Router>
      );

      // Should trigger redirect because user is authenticated
      expect(history.location.pathname).toBe('/');
    });

    it('should access isLoading state from useAuth', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: true,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Signing in...')).toBeInTheDocument();
    });

    it('should access error state from useAuth', () => {
      const mockError = new Error('Test error');

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: mockError,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText(/Authentication failed/)).toBeInTheDocument();
    });
  });
});
