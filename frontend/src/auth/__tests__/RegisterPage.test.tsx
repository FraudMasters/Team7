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

// Mock useAuth from react-oidc-context
vi.mock('react-oidc-context', () => ({
  useAuth: vi.fn(),
}));

const { useAuth } = require('react-oidc-context');

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render registration form correctly', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Create Account')).toBeInTheDocument();
      expect(screen.getByText(/Join the AgentHR platform today/)).toBeInTheDocument();
    });

    it('should render email input field', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText(/enter your email/i)).toBeInTheDocument();
    });

    it('should render password input field', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText(/create a password/i)).toBeInTheDocument();
    });

    it('should render confirm password input field', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByPlaceholderText(/confirm your password/i)).toBeInTheDocument();
    });

    it('should render create account button', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const signUpButton = screen.getByRole('button', { name: /create account/i });
      expect(signUpButton).toBeInTheDocument();
    });

    it('should render link to login page', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByText(/Already have an account\?/i)).toBeInTheDocument();
      expect(screen.getByText('Sign in')).toBeInTheDocument();
    });

    it('should render terms and conditions checkbox', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByRole('checkbox')).toBeInTheDocument();
      expect(screen.getByText(/Terms of Service/i)).toBeInTheDocument();
      expect(screen.getByText(/Privacy Policy/i)).toBeInTheDocument();
    });

    it('should display email verification info alert', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByText(/After registration, you'll receive a verification email/)).toBeInTheDocument();
    });
  });

  describe('Email Validation', () => {
    it('should show error for invalid email format', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const emailInput = screen.getByPlaceholderText(/enter your email/i);
      await user.type(emailInput, 'invalidemail');

      const signUpButton = screen.getByRole('button', { name: /create account/i });
      await user.click(signUpButton);

      // Should show email format validation error
      await waitFor(() => {
        const errorMessage = screen.queryByText(/Please enter a valid email address/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should accept valid email format', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const emailInput = screen.getByPlaceholderText(/enter your email/i);
      await user.type(emailInput, 'test@example.com');

      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      await user.type(passwordInput, 'password123');

      const confirmPasswordInput = screen.getByPlaceholderText(/confirm your password/i);
      await user.type(confirmPasswordInput, 'password123');

      const termsCheckbox = screen.getByRole('checkbox');
      await user.click(termsCheckbox);

      // Should not show email format error when form is valid
      expect(screen.queryByText(/Please enter a valid email address/i)).not.toBeInTheDocument();
    });

    it('should require email field', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter
      );

      const signUpButton = screen.getByRole('button', { name: /create account/i });
      await user.click(signUpButton);

      // Should show required field error
      await waitFor(() => {
        const errorMessage = screen.queryByText(/Email is required/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });
  });

  describe('Password Validation', () => {
    it('should enforce minimum password length of 8 characters', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      await user.type(passwordInput, 'short');

      const signUpButton = screen.getByRole('button', { name: /create account/i });
      await user.click(signUpButton);

      await waitFor(() => {
        const errorMessage = screen.queryByText(/Password must be at least 8 characters/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should accept valid password length', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      await user.type(passwordInput, 'password123');

      expect(screen.queryByText(/Password must be at least 8 characters/i)).not.toBeInTheDocument();
    });

    it('should show password strength indicator', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/create a password/i);

      // Type weak password
      await user.type(passwordInput, 'password');
      await waitFor(() => {
        expect(screen.getByText('Weak')).toBeInTheDocument();
      });

      // Clear and type stronger password
      await user.clear(passwordInput);
      await user.type(passwordInput, 'Str0ng!P@ss');
      await waitFor(() => {
        expect(screen.getByText('Strong')).toBeInTheDocument();
      });
    });
  });

  describe('Password Confirmation', () => {
    it('should require passwords to match', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      const confirmPasswordInput = screen.getByPlaceholderText(/confirm your password/i);

      await user.type(passwordInput, 'password123');
      await user.type(confirmPasswordInput, 'differentpassword');

      const signUpButton = screen.getByRole('button', { name: /create account/i });
      await user.click(signUpButton);

      await waitFor(() => {
        const errorMessage = screen.queryByText(/Passwords do not match/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should accept matching passwords', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      const confirmPasswordInput = screen.getByPlaceholderText(/confirm your password/i);

      await user.type(passwordInput, 'password123');
      await user.type(confirmPasswordInput, 'password123');

      expect(screen.queryByText(/Passwords do not match/i)).not.toBeInTheDocument();
    });

    it('should show error when confirm password is empty', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      await user.type(passwordInput, 'password123');

      const signUpButton = screen.getByRole('button', { name: /create account/i });
      await user.click(signUpButton);

      await waitFor(() => {
        const errorMessage = screen.queryByText(/Please confirm your password/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });
  });

  describe('Terms Agreement', () => {
    it('should require terms checkbox to be checked', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      // Fill form with valid data but don't check terms
      await user.type(screen.getByPlaceholderText(/enter your email/i), 'test@example.com');
      await user.type(screen.getByPlaceholderText(/create a password/i), 'password123');
      await user.type(screen.getByPlaceholderText(/confirm your password/i), 'password123');

      const signUpButton = screen.getByRole('button', { name: /create account/i });
      await user.click(signUpButton);

      await waitFor(() => {
        const errorMessage = screen.queryByText(/You must agree to the terms and conditions/i);
        expect(errorMessage).toBeInTheDocument();
      });
    });

    it('should allow form submission when terms are agreed', async () => {
      const user = userEvent.setup();
      const mockSigninRedirect = vi.fn();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: mockSigninRedirect,
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter
      );

      // Fill form and check terms
      await user.type(screen.getByPlaceholderText(/enter your email/i), 'test@example.com');
      await user.type(screen.getByPlaceholderText(/create a password/i), 'password123');
      await user.type(screen.getByPlaceholderText(/confirm your password/i), 'password123');

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

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <Router location={history.location} navigator={history}>
          <RegisterPage />
        </Router>
      );

      const signInLink = screen.getByText('Sign in');
      await user.click(signInLink);

      expect(history.location.pathname).toBe('/auth/login');
    });
  });

  describe('Redirect Behavior', () => {
    it('should redirect authenticated users to home page', async () => {
      const history = createMemoryHistory();
      history.push('/register');

      useAuth.mockReturnValue({
        user: { profile: { sub: '123' } },
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
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
      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
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

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      await user.type(passwordInput, 'password');

      await waitFor(() => {
        const strengthIndicator = screen.getByText('Weak');
        expect(strengthIndicator).toBeInTheDocument();
      });
    });

    it('should show "Fair" for moderate passwords', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      await user.type(passwordInput, 'Password1');

      await waitFor(() => {
        const strengthIndicator = screen.getByText('Fair');
        expect(strengthIndicator).toBeInTheDocument();
      });
    });

    it('should show "Good" for strong passwords', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      await user.type(passwordInput, 'P@ssword123');

      await waitFor(() => {
        const strengthIndicator = screen.getByText('Good');
        expect(strengthIndicator).toBeInTheDocument();
      });
    });

    it('should show "Strong" for very strong passwords', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      await user.type(passwordInput, 'Str0ng!P@ssw0rd#2026');

      await waitFor(() => {
        const strengthIndicator = screen.getByText('Strong');
        expect(strengthIndicator).toBeInTheDocument();
      });
    });
  });

  describe('Form Integration', () => {
    it('should allow typing in all form fields', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const emailInput = screen.getByPlaceholderText(/enter your email/i);
      const passwordInput = screen.getByPlaceholderText(/create a password/i);
      const confirmPasswordInput = screen.getByPlaceholderText(/confirm your password/i);

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.type(confirmPasswordInput, 'password123');

      expect(emailInput).toHaveValue('test@example.com');
      expect(passwordInput).toHaveValue('password123');
      expect(confirmPasswordInput).toHaveValue('password123');
    });

    it('should clear field errors when user starts typing', async () => {
      const user = userEvent.setup();

      useAuth.mockReturnValue({
        user: null,
        isLoading: false,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter
      );

      // Trigger validation error
      const signUpButton = screen.getByRole('button', { name: /create account/i });
      await user.click(signUpButton);

      // Check that error appears
      await waitFor(() => {
        expect(screen.queryByText(/Email is required/i)).toBeInTheDocument();
      });

      // Start typing in email field
      const emailInput = screen.getByPlaceholderText(/enter your email/i);
      await user.type(emailInput, 'test');

      // Error should be cleared
      expect(screen.queryByText(/Email is required/i)).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should disable form while loading', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: true,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      const signUpButton = screen.getByRole('button', { name: /creating account/i });
      expect(signUpButton).toBeDisabled();
    });

    it('should show loading text on button while loading', () => {
      useAuth.mockReturnValue({
        user: null,
        isLoading: true,
        error: null,
        signinRedirect: vi.fn(),
      });

      render(
        <MemoryRouter>
          <RegisterPage />
        </MemoryRouter>
      );

      expect(screen.getByText('Creating account...')).toBeInTheDocument();
    });
  });
});
