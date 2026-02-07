/**
 * Unit tests for RegisterPage component
 *
 * Tests cover registration form rendering, validation,
 * password strength indicator, and navigation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { MemoryRouter, Router } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import RegisterPage from '../RegisterPage';

// Mock useAuthContext
vi.mock('@/contexts/AuthContext', () => ({
  useAuthContext: vi.fn(),
}));

const { useAuthContext } = require('@/contexts/AuthContext');

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render registration form correctly', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Create Account')).toBeInTheDocument();
      expect(screen.getByText(/Sign up to get started/)).toBeInTheDocument();
    });

    it('should render email input field', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText(/email address/i)).toBeInTheDocument();
    });

    it('should render password input field', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
    });

    it('should render confirm password input field', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText(/confirm password/i)).toBeInTheDocument();
    });

    it('should render sign up button', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const signUpButton = screen.getByRole('button', { name: /sign up/i });
      expect(signUpButton).toBeInTheDocument();
    });

    it('should render link to login page', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const loginLink = screen.getByText(/already have an account/i);
      expect(loginLink).toBeInTheDocument();
      expect(screen.getByText('Sign in')).toBeInTheDocument();
    });

    it('should render terms and conditions checkbox', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByRole('checkbox')).toBeInTheDocument();
      expect(screen.getByText(/I agree to the terms and conditions/i)).toBeInTheDocument();
    });
  });

  describe('Email Validation', () => {
    it('should show error for invalid email format', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const emailInput = screen.getByPlaceholderText(/email address/i);
      await user.type(emailInput, 'invalidemail');
      await user.tab(); // Trigger blur

      // Should show email format validation error
      await waitFor(() => {
        const errorMessage = screen.queryByText(/invalid email format/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should accept valid email format', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const emailInput = screen.getByPlaceholderText(/email address/i);
      await user.type(emailInput, 'test@example.com');
      await user.tab();

      // Should not show email format error
      expect(screen.queryByText(/invalid email format/i)).not.toBeInTheDocument();
    });

    it('should require email field', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const signUpButton = screen.getByRole('button', { name: /sign up/i });
      await user.click(signUpButton);

      // Should show required field error
      await waitFor(() => {
        const errorMessage = screen.queryByText(/email is required/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });
  });

  describe('Password Validation', () => {
    it('should enforce minimum password length of 8 characters', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);
      await user.type(passwordInput, 'short');
      await user.tab();

      await waitFor(() => {
        const errorMessage = screen.queryByText(/password must be at least 8 characters/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should accept valid password length', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);
      await user.type(passwordInput, 'password123');
      await user.tab();

      expect(screen.queryByText(/password must be at least 8 characters/i)).not.toBeInTheDocument();
    });

    it('should show password strength indicator', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);

      // Type weak password
      await user.type(passwordInput, 'password');
      await waitFor(() => {
        expect(screen.getByText(/weak/i)).toBeInTheDocument();
      });

      // Clear and type stronger password
      await user.clear(passwordInput);
      await user.type(passwordInput, 'P@ssw0rd123!');
      await waitFor(() => {
        expect(screen.getByText(/strong/i)).toBeInTheDocument();
      });
    });
  });

  describe('Password Confirmation', () => {
    it('should require passwords to match', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);
      const confirmPasswordInput = screen.getByPlaceholderText(/confirm password/i);

      await user.type(passwordInput, 'password123');
      await user.type(confirmPasswordInput, 'differentpassword');
      await user.tab();

      await waitFor(() => {
        const errorMessage = screen.queryByText(/passwords do not match/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should accept matching passwords', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);
      const confirmPasswordInput = screen.getByPlaceholderText(/confirm password/i);

      await user.type(passwordInput, 'password123');
      await user.type(confirmPasswordInput, 'password123');
      await user.tab();

      expect(screen.queryByText(/passwords do not match/i)).not.toBeInTheDocument();
    });

    it('should show error when confirm password is empty', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);
      await user.type(passwordInput, 'password123');

      const confirmPasswordInput = screen.getByPlaceholderText(/confirm password/i);
      await user.tab();

      await waitFor(() => {
        const errorMessage = screen.queryByText(/please confirm your password/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });
  });

  describe('Terms Agreement', () => {
    it('should require terms checkbox to be checked', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      // Fill form with valid data but don't check terms
      await user.type(screen.getByPlaceholderText(/email address/i), 'test@example.com');
      await user.type(screen.getByPlaceholderText(/password/i), 'password123');
      await user.type(screen.getByPlaceholderText(/confirm password/i), 'password123');

      const signUpButton = screen.getByRole('button', { name: /sign up/i });
      await user.click(signUpButton);

      await waitFor(() => {
        const errorMessage = screen.queryByText(/you must agree to the terms and conditions/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should allow form submission when terms are agreed', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      // Fill form and check terms
      await user.type(screen.getByPlaceholderText(/email address/i), 'test@example.com');
      await user.type(screen.getByPlaceholderText(/password/i), 'password123');
      await user.type(screen.getByPlaceholderText(/confirm password/i), 'password123');

      const termsCheckbox = screen.getByRole('checkbox');
      await user.click(termsCheckbox);

      expect(termsCheckbox).toBeChecked();
    });
  });

  describe('Navigation', () => {
    it('should navigate to login page when sign in link is clicked', async () => {
      const user = userEvent.setup();
      const history = createMemoryHistory();
      history.push('/register');

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <Router location={history.location} navigator={history}>
          <RegisterPage />
        </Router>
      );

      const signInLink = screen.getByText('Sign in');
      await user.click(signInLink);

      expect(history.location.pathname).toBe('/login');
    });
  });

  describe('Email Verification Info', () => {
    it('should display email verification information', () => {
      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByText(/email verification/i)).toBeInTheDocument();
      expect(screen.getByText(/we'll send you a verification link/i)).toBeInTheDocument();
    });
  });

  describe('Redirect Behavior', () => {
    it('should redirect authenticated users to home page', async () => {
      const history = createMemoryHistory();
      history.push('/register');

      useAuthContext.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <Router location={history.location} navigator={history}>
          <RegisterPage />
        </Router>
      );

      await waitFor(() => {
        expect(history.location.pathname).toBe('/');
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
      history.push('/register');

      render(
        <Router location={history.location} navigator={history}>
          <RegisterPage />
        </Router>
      );

      expect(history.location.pathname).toBe('/register');
    });
  });

  describe('Password Strength Indicator', () => {
    it('should show "Weak" for simple passwords', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);
      await user.type(passwordInput, 'password');

      await waitFor(() => {
        const strengthIndicator = screen.getByText(/weak/i);
        expect(strengthIndicator).toBeInTheDocument();
      });
    });

    it('should show "Fair" for moderate passwords', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);
      await user.type(passwordInput, 'Password1');

      await waitFor(() => {
        const strengthIndicator = screen.getByText(/fair/i);
        expect(strengthIndicator).toBeInTheDocument();
      });
    });

    it('should show "Good" for strong passwords', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);
      await user.type(passwordInput, 'P@ssword123');

      await waitFor(() => {
        const strengthIndicator = screen.getByText(/good/i);
        expect(strengthIndicator).toBeInTheDocument();
      });
    });

    it('should show "Strong" for very strong passwords', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter
      );

      const passwordInput = screen.getByPlaceholderText(/password/i);
      await user.type(passwordInput, 'Str0ng!P@ssw0rd#2026');

      await waitFor(() => {
        const strengthIndicator = screen.getByText(/strong/i);
        expect(strengthIndicator).toBeInTheDocument();
      });
    });
  });

  describe('Form Integration', () => {
    it('should allow typing in all form fields', async () => {
      const user = userEvent.setup();

      useAuthContext.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        error: null,
        login: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const emailInput = screen.getByPlaceholderText(/email address/i);
      const passwordInput = screen.getByPlaceholderText(/password/i);
      const confirmPasswordInput = screen.getByPlaceholderText(/confirm password/i);

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.type(confirmPasswordInput, 'password123');

      expect(emailInput).toHaveValue('test@example.com');
      expect(passwordInput).toHaveValue('password123');
      expect(confirmPasswordInput).toHaveValue('password123');
    });
  });
});
