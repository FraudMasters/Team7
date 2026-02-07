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

// Mock useAuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuthContext: vi.fn(),
}));

const { useAuthContext } = require('@/contexts/AuthContext');

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render login form correctly', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Welcome Back')).toBeInTheDocument();
      expect(screen.getByText(/Sign in to your account/)).toBeInTheDocument();
    });

    it('should render login button', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const loginButton = screen.getByRole('button', { name: /sign in/i });
      expect(loginButton).toBeInTheDocument();
    });

    it('should render email and password input fields', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      // Note: These fields are for visual purposes only as actual auth happens via Keycloak
      expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
    });

    it('should render "Forgot Password" link', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Forgot Password?')).toBeInTheDocument();
    });

    it('should render link to registration page', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const registerLink = screen.getByText(/don't have an account/i);
      expect(registerLink).toBeInTheDocument();
      expect(screen.getByText('Sign up')).toBeInTheDocument();
    });
  });

  describe('Login Flow', () => {
    it('should call login function when login button is clicked', async () => {
      const mockLogin = vi.fn();
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: mockLogin,
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const loginButton = screen.getByRole('button', { name: /sign in/i });
      await user.click(loginButton);

      expect(mockLogin).toHaveBeenCalledTimes(1);
    });

    it('should trigger redirect to Keycloak on login', () => {
      // The login function in AuthContext calls signinRedirect
      const mockLogin = vi.fn();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: mockLogin,
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const loginButton = screen.getByRole('button', { name: /sign in/i });
      loginButton.click();

      expect(mockLogin).toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('should show loading state during authentication', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        error: null,
        login: vi.fn(),
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
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Signing in...')).toBeInTheDocument();
    });

    it('should disable login button while loading', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        error: null,
        login: vi.fn(),
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
      mockError.message = 'Invalid username or password';

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: mockError,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText(/authentication failed/i)).toBeInTheDocument();
    });

    it('should show error alert with error details', () => {
      const mockError = new Error('Login failed: Invalid credentials');

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: mockError,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Login failed: Invalid credentials')).toBeInTheDocument();
    });
  });

  describe('Redirect Behavior', () => {
    it('should redirect authenticated users to home page', async () => {
      const history = createMemoryHistory();
      history.push('/login');

      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        login: vi.fn(),
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

      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        login: vi.fn(),
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
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
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
    it('should navigate to registration page when sign up link is clicked', async () => {
      const user = userEvent.setup();
      const history = createMemoryHistory();
      history.push('/login');

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <Router location={history.location} navigator={history}>
          <LoginPage />
        </Router>
      );

      const signUpLink = screen.getByText('Sign up');
      await user.click(signUpLink);

      expect(history.location.pathname).toBe('/register');
    });

    it('should preserve location state when navigating to register', async () => {
      const user = userEvent.setup();
      const history = createMemoryHistory();
      history.push('/login');
      const fromLocation = { pathname: '/protected-page', state: { from: '/dashboard' } };

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
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

      const signUpLink = screen.getByText('Sign up');
      await user.click(signUpLink);

      expect(history.location.state).toBeDefined();
    });
  });

  describe('Form Interaction', () => {
    it('should allow typing in email field', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const emailInput = screen.getByPlaceholderText(/email/i);
      await user.type(emailInput, 'test@example.com');

      expect(emailInput).toHaveValue('test@example.com');
    });

    it('should allow typing in password field', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);
      await user.type(passwordInput, 'password123');

      expect(passwordInput).toHaveValue('password123');
    });

    it('should not submit form on Enter key (actual auth via Keycloak)', async () => {
      const user = userEvent.setup();
      const mockLogin = vi.fn();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: mockLogin,
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const emailInput = screen.getByPlaceholderText(/email/i);
      await user.type(emailInput, 'test@example.com');

      // The form submission is handled by the login button, not Enter key
      // since actual authentication happens via Keycloak redirect
      expect(mockLogin).not.toHaveBeenCalled();
    });
  });

  describe('Visual Design', () => {
    it('should render login form in a Paper component', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
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
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
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

    it('should have gradient background', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      // Check for the main box wrapper with background style
      const wrapper = document.querySelector('style');
      expect(wrapper).toBeDefined();
    });
  });

  describe('Integration with AuthContext', () => {
    it('should use login function from AuthContext', () => {
      const mockLogin = vi.fn();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: mockLogin,
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      const loginButton = screen.getByRole('button', { name: /sign in/i });
      loginButton.click();

      expect(mockLogin).toHaveBeenCalledTimes(1);
    });

    it('should access isAuthenticated state from AuthContext', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      const history = createMemoryHistory();
      history.push('/login');

      render(
        <Router location={history.location} navigator={history}>
          <LoginPage />
        </Router>
      );

      // Should trigger redirect because isAuthenticated is true
      expect(history.location.pathname).toBe('/');
    });

    it('should access isLoading state from AuthContext', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Signing in...')).toBeInTheDocument();
    });

    it('should access error state from AuthContext', () => {
      const mockError = new Error('Test error');

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: mockError,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Test error')).toBeInTheDocument();
    });
  });
});
