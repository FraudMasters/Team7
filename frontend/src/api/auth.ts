/**
 * Authentication API
 *
 * This module provides API functions for user authentication including
 * registration, login, token refresh, logout, and password reset.
 *
 * @example
 * ```ts
 * import { register, login, logout, refreshToken } from '@/api/auth';
 *
 * // Register a new user
 * const user = await register({
 *   email: 'user@example.com',
 *   password: 'SecurePass123!',
 *   full_name: 'John Doe'
 * });
 *
 * // Login
 * const session = await login('user@example.com', 'SecurePass123!');
 * console.log(session.access_token);
 *
 * // Refresh token
 * const newToken = await refreshToken(session.refresh_token);
 *
 * // Logout
 * await logout(session.refresh_token);
 * ```
 */

import { apiClient } from '@/api/client';
import type {
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  LoginResponse,
  RefreshTokenRequest,
  RefreshTokenResponse,
  LogoutRequest,
  LogoutResponse,
  PasswordResetRequest,
  PasswordResetRequestResponse,
  PasswordResetConfirmRequest,
  PasswordResetConfirmResponse,
  ApiError,
} from '@/types/api';

/**
 * Register a new user account
 *
 * Creates a new user account with the provided email and password.
 * The password must be at least 8 characters and include uppercase,
 * lowercase, digit, and special character. A default 'viewer' role
 * will be assigned to the new user.
 *
 * @param request - Registration data including email, password, and optional full_name
 * @returns Promise resolving to registration response with user information
 * @throws ApiError if registration fails (email already exists, weak password, etc.)
 *
 * @example
 * ```ts
 * const result = await register({
 *   email: 'user@example.com',
 *   password: 'SecurePass123!',
 *   full_name: 'John Doe'
 * });
 * console.log(result.message); // "User registered successfully"
 * console.log(result.user.email); // "user@example.com"
 * ```
 */
export async function register(
  request: RegisterRequest
): Promise<RegisterResponse> {
  try {
    const response = await apiClient
      .getAxiosInstance()
      .post<RegisterResponse>('/api/auth/register', request);
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to register user'
    );
  }
}

/**
 * Login with email and password
 *
 * Authenticates a user with their email and password. Returns JWT
 * access token (short-lived) and refresh token (long-lived) along
 * with user information.
 *
 * @param email - User's email address
 * @param password - User's password
 * @returns Promise resolving to login response with tokens and user info
 * @throws ApiError if login fails (invalid credentials, inactive account, etc.)
 *
 * @example
 * ```ts
 * const session = await login('user@example.com', 'SecurePass123!');
 * console.log(session.access_token); // JWT access token
 * console.log(session.refresh_token); // JWT refresh token
 * console.log(session.expires_in); // Token expiration in seconds (default: 1800)
 * console.log(session.user.email); // "user@example.com"
 * ```
 */
export async function login(
  email: string,
  password: string
): Promise<LoginResponse> {
  try {
    const request: LoginRequest = { email, password };
    const response = await apiClient
      .getAxiosInstance()
      .post<LoginResponse>('/api/auth/login', request);
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to login'
    );
  }
}

/**
 * Refresh access token using refresh token
 *
 * Obtains a new access token using a valid refresh token. Use this
 * to maintain user session when the access token expires.
 *
 * @param refreshToken - Valid refresh token from login
 * @returns Promise resolving to refresh response with new access token
 * @throws ApiError if refresh fails (invalid token, expired token, revoked token, etc.)
 *
 * @example
 * ```ts
 * const newToken = await refreshToken(refreshToken);
 * console.log(newToken.access_token); // New JWT access token
 * console.log(newToken.expires_in); // Expiration in seconds (default: 1800)
 * ```
 */
export async function refreshToken(
  refreshToken: string
): Promise<RefreshTokenResponse> {
  try {
    const request: RefreshTokenRequest = { refresh_token: refreshToken };
    const response = await apiClient
      .getAxiosInstance()
      .post<RefreshTokenResponse>('/api/auth/refresh', request);
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to refresh token'
    );
  }
}

/**
 * Logout and revoke refresh token
 *
 * Invalidates the refresh token on the server, effectively logging
 * out the user. The client should also clear stored tokens.
 *
 * @param refreshToken - Refresh token to revoke
 * @returns Promise resolving to logout response
 * @throws ApiError if logout fails
 *
 * @example
 * ```ts
 * await logout(refreshToken);
 * console.log('Logged out successfully');
 * // Clear tokens from localStorage
 * localStorage.removeItem('access_token');
 * localStorage.removeItem('refresh_token');
 * ```
 */
export async function logout(
  refreshToken: string
): Promise<LogoutResponse> {
  try {
    const request: LogoutRequest = { refresh_token: refreshToken };
    const response = await apiClient
      .getAxiosInstance()
      .post<LogoutResponse>('/api/auth/logout', request);
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to logout'
    );
  }
}

/**
 * Request password reset
 *
 * Initiates the password reset flow by sending a reset token to the
 * user's email. The reset token will be valid for 1 hour.
 * Note: For security, this endpoint returns the same message whether
 * the email exists or not (prevents email enumeration).
 *
 * @param email - User's email address
 * @returns Promise resolving to password reset request response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const result = await passwordResetRequest('user@example.com');
 * console.log(result.message); // "Password reset email sent"
 * ```
 */
export async function passwordResetRequest(
  email: string
): Promise<PasswordResetRequestResponse> {
  try {
    const request: PasswordResetRequest = { email };
    const response = await apiClient
      .getAxiosInstance()
      .post<PasswordResetRequestResponse>(
        '/api/auth/password-reset-request',
        request
      );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to request password reset'
    );
  }
}

/**
 * Confirm password reset with token
 *
 * Completes the password reset flow by validating the reset token
 * and updating the user's password. The new password must meet the
 * same strength requirements as registration (8+ chars, uppercase,
 * lowercase, digit, special character).
 *
 * @param token - Password reset token from email
 * @param newPassword - New password to set
 * @returns Promise resolving to password reset confirm response
 * @throws ApiError if confirmation fails (invalid token, expired token, weak password, etc.)
 *
 * @example
 * ```ts
 * const result = await passwordResetConfirm('reset_token_here', 'NewSecurePass123!');
 * console.log(result.message); // "Password reset successfully"
 * ```
 */
export async function passwordResetConfirm(
  token: string,
  newPassword: string
): Promise<PasswordResetConfirmResponse> {
  try {
    const request: PasswordResetConfirmRequest = {
      token,
      new_password: newPassword,
    };
    const response = await apiClient
      .getAxiosInstance()
      .post<PasswordResetConfirmResponse>(
        '/api/auth/password-reset-confirm',
        request
      );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to confirm password reset'
    );
  }
}
