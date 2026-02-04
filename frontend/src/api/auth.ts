/**
 * Authentication API Client
 *
 * This module provides a typed client for authentication-related API operations.
 * Handles user registration, login, logout, token refresh, email verification,
 * and password reset functionality.
 *
 * @example
 * ```ts
 * import { authClient } from '@/api/auth';
 *
 * // Register a new user
 * const result = await authClient.register({
 *   email: 'user@example.com',
 *   password: 'SecurePass123',
 *   name: 'John Doe',
 * });
 *
 * // Login
 * const loginResult = await authClient.login({
 *   email: 'user@example.com',
 *   password: 'SecurePass123',
 * });
 * console.log(loginResult.access_token);
 *
 * // Get current user
 * const user = await authClient.getCurrentUser();
 * console.log(user.name);
 *
 * // Refresh token
 * const tokens = await authClient.refreshToken('refresh-token');
 * console.log(tokens.access_token);
 *
 * // Logout
 * await authClient.logout();
 *
 * // Forgot password
 * await authClient.forgotPassword('user@example.com');
 *
 * // Reset password
 * await authClient.resetPassword('reset-token', 'NewSecurePass123');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError, ApiClientConfig } from '@/types/api';

/**
 * User information response
 */
export interface UserInfo {
  id: string;
  email: string;
  name: string;
  role: 'Admin' | 'Recruiter' | 'Viewer';
  is_active: boolean;
  email_verified: boolean;
}

/**
 * User registration request
 */
export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

/**
 * User registration response
 */
export interface RegisterResponse {
  message: string;
  user: UserInfo;
}

/**
 * User login request
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * User login response
 */
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserInfo;
}

/**
 * Token refresh response
 */
export interface TokenRefreshResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * Logout response
 */
export interface LogoutResponse {
  message: string;
}

/**
 * Email verification request
 */
export interface VerifyEmailRequest {
  token: string;
}

/**
 * Email verification response
 */
export interface VerifyEmailResponse {
  message: string;
  email_verified: boolean;
}

/**
 * Forgot password request
 */
export interface ForgotPasswordRequest {
  email: string;
}

/**
 * Forgot password response
 */
export interface ForgotPasswordResponse {
  message: string;
}

/**
 * Reset password request
 */
export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

/**
 * Reset password response
 */
export interface ResetPasswordResponse {
  message: string;
}

/**
 * Get current user response
 */
export interface GetCurrentUserResponse extends UserInfo {}

/**
 * Default API configuration
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 30000, // 30 seconds for auth operations
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Authentication API Client class
 *
 * Provides typed methods for all authentication API endpoints with proper
 * error handling and type safety.
 */
export class AuthClient {
  private client: AxiosInstance;

  /**
   * Create a new Auth client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config: ApiClientConfig = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Request interceptor - add auth token to all requests
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(this.transformError(error));
      }
    );

    // Response interceptor - handle 401 errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearAuthToken();
        }
        return Promise.reject(this.transformError(error));
      }
    );
  }

  /**
   * Get the JWT token from localStorage
   *
   * @returns JWT token or null if not found
   */
  private getAuthToken = (): string | null => {
    try {
      return localStorage.getItem('auth_token');
    } catch {
      return null;
    }
  };

  /**
   * Remove the JWT token from localStorage
   * Called on 401 responses to clear invalid tokens
   */
  private clearAuthToken = (): void => {
    try {
      localStorage.removeItem('auth_token');
    } catch {
      // Silently fail if localStorage is unavailable
    }
  };

  /**
   * Transform Axios error to standardized API error
   *
   * @param error - Axios error
   * @returns Transformed API error
   */
  private transformError(error: unknown): ApiError {
    const axiosError = error as AxiosError<{ detail?: string }>;

    // Network error (no response)
    if (!axiosError.response) {
      if (axiosError.code === 'ECONNABORTED') {
        return {
          detail: 'Request timeout. Please check your connection and try again.',
          status: 408,
        };
      }
      return {
        detail: 'Network error. Please check your connection and try again.',
        status: 0,
      };
    }

    // Server returned error response
    const status = axiosError.response.status;
    const data = axiosError.response.data;

    // Use server's error message if available
    if (data?.detail) {
      return { detail: data.detail, status };
    }

    // Default error messages by status code
    const defaultMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      422: 'Validation error. Please check your input.',
      429: 'Too many requests. Please try again later.',
      500: 'Server error. Please try again later.',
      502: 'Bad gateway. Please try again later.',
      503: 'Service unavailable. Please try again later.',
    };

    return {
      detail: data?.detail || defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * Register a new user account
   *
   * Creates a new user with the provided email, password, and name.
   * The user will be assigned a default role (Recruiter).
   *
   * @param request - Registration data with email, password, and name
   * @returns Registration response with success message and user information
   * @throws ApiError if registration fails
   *
   * @example
   * ```ts
   * const result = await authClient.register({
   *   email: 'john@example.com',
   *   password: 'SecurePass123',
   *   name: 'John Doe',
   * });
   * console.log(result.user.id);
   * ```
   */
  async register(request: RegisterRequest): Promise<RegisterResponse> {
    try {
      const response: AxiosResponse<RegisterResponse> = await this.client.post(
        '/api/auth/register',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Authenticate a user with email and password
   *
   * Validates the user's credentials and returns JWT tokens for authentication.
   * The access token is short-lived (default 30 minutes) and the refresh token
   * is long-lived (default 7 days).
   *
   * @param request - Login credentials with email and password
   * @returns Login response with access token, refresh token, and user information
   * @throws ApiError if login fails
   *
   * @example
   * ```ts
   * const result = await authClient.login({
   *   email: 'john@example.com',
   *   password: 'SecurePass123',
   * });
   * console.log(result.access_token);
   * console.log(result.user.name);
   * ```
   */
  async login(request: LoginRequest): Promise<LoginResponse> {
    try {
      const response: AxiosResponse<LoginResponse> = await this.client.post(
        '/api/auth/login',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Logout the current user and invalidate refresh token
   *
   * Clears the current session by invalidating the refresh token on the server.
   * The client should also clear local token storage.
   *
   * @returns Logout response with success message
   * @throws ApiError if logout fails
   *
   * @example
   * ```ts
   * await authClient.logout();
   * // Clear local storage
   * localStorage.removeItem('auth_token');
   * ```
   */
  async logout(): Promise<LogoutResponse> {
    try {
      const response: AxiosResponse<LogoutResponse> = await this.client.post(
        '/api/auth/logout'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Refresh access token using refresh token
   *
   * Obtains a new access token using a valid refresh token.
   * This should be called when the access token expires.
   *
   * @param refreshToken - Valid refresh token
   * @returns Token refresh response with new access and refresh tokens
   * @throws ApiError if refresh fails
   *
   * @example
   * ```ts
   * const result = await authClient.refreshToken('your-refresh-token');
   * console.log(result.access_token);
   * // Update local storage with new tokens
   * ```
   */
  async refreshToken(refreshToken: string): Promise<TokenRefreshResponse> {
    try {
      const response: AxiosResponse<TokenRefreshResponse> = await this.client.post(
        '/api/auth/refresh',
        { refresh_token: refreshToken }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get the currently authenticated user's information
   *
   * Returns the user profile for the currently authenticated user.
   * Requires a valid access token.
   *
   * @returns Current user information
   * @throws ApiError if request fails or user is not authenticated
   *
   * @example
   * ```ts
   * const user = await authClient.getCurrentUser();
   * console.log(user.name, user.role);
   * ```
   */
  async getCurrentUser(): Promise<GetCurrentUserResponse> {
    try {
      const response: AxiosResponse<GetCurrentUserResponse> = await this.client.get(
        '/api/auth/me'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Verify user email with token
   *
   * Verifies the user's email address using a token sent to their email.
   * This is typically called from a link in the verification email.
   *
   * @param request - Email verification request with token
   * @returns Email verification response with success status
   * @throws ApiError if verification fails
   *
   * @example
   * ```ts
   * const result = await authClient.verifyEmail({ token: 'verify-token' });
   * console.log(result.email_verified);
   * ```
   */
  async verifyEmail(request: VerifyEmailRequest): Promise<VerifyEmailResponse> {
    try {
      const response: AxiosResponse<VerifyEmailResponse> = await this.client.post(
        '/api/auth/verify-email',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Request a password reset email
   *
   * Initiates the password reset flow by sending an email with a reset link
   * to the user's email address.
   *
   * @param request - Forgot password request with email
   * @returns Forgot password response with success message
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * await authClient.forgotPassword({ email: 'user@example.com' });
   * console.log('Password reset email sent');
   * ```
   */
  async forgotPassword(request: ForgotPasswordRequest): Promise<ForgotPasswordResponse> {
    try {
      const response: AxiosResponse<ForgotPasswordResponse> = await this.client.post(
        '/api/auth/forgot-password',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Reset password with token
   *
   * Resets the user's password using a token from the password reset email.
   * The token is typically included as a query parameter in the reset link.
   *
   * @param token - Password reset token from email
   * @param newPassword - New password to set
   * @returns Reset password response with success message
   * @throws ApiError if reset fails
   *
   * @example
   * ```ts
   * await authClient.resetPassword('reset-token', 'NewSecurePass123');
   * console.log('Password reset successful');
   * ```
   */
  async resetPassword(
    token: string,
    newPassword: string
  ): Promise<ResetPasswordResponse> {
    try {
      const response: AxiosResponse<ResetPasswordResponse> = await this.client.post(
        '/api/auth/reset-password',
        { token, new_password: newPassword }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get the underlying Axios instance
   *
   * This is useful for making custom requests not covered by the convenience methods.
   *
   * @returns Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }
}

/**
 * Default authentication client instance
 *
 * Use this singleton instance for all authentication API calls.
 */
export const authClient = new AuthClient();

/**
 * Export authentication client class for custom instances
 */
export default AuthClient;
