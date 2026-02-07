/**
 * Two-Factor Authentication API Client
 *
 * This module provides a typed client for two-factor authentication (2FA) operations
 * including setup, verification, disabling, and backup code generation.
 *
 * @example
 * ```ts
 * import { twoFactorClient } from '@/api/twoFactor';
 *
 * // Check 2FA status
 * const status = await twoFactorClient.getStatus('user-123');
 *
 * // Setup 2FA with TOTP
 * const setup = await twoFactorClient.setup({
 *   user_id: 'user-123',
 *   method: 'totp',
 * });
 * // Display setup.backup_codes and setup.provisioning_uri (QR code)
 *
 * // Verify 2FA code
 * const verify = await twoFactorClient.verify({
 *   user_id: 'user-123',
 *   code: '123456',
 * });
 *
 * // Disable 2FA
 * await twoFactorClient.disable({
 *   user_id: 'user-123',
 *   code: '123456',
 * });
 *
 * // Generate new backup codes
 * const backup = await twoFactorClient.generateBackupCodes({
 *   user_id: 'user-123',
 *   code: '123456',
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import {
  trackApiCall,
  type PerformanceStats,
  getPerformanceStats as getPerformanceStatsUtil,
} from '@/utils/performanceTracker';
import type {
  TwoFactorStatusResponse,
  TwoFactorSetupRequest,
  TwoFactorSetupResponse,
  TwoFactorVerifyRequest,
  TwoFactorVerifyResponse,
  TwoFactorDisableRequest,
  BackupCodesGenerateRequest,
  BackupCodesResponse,
  ApiError,
  ApiClientConfig,
} from '@/types/api';

/**
 * Default 2FA API configuration
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 30000, // 30 seconds for 2FA operations
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Two-Factor Authentication API Client class
 *
 * Provides methods for 2FA operations with proper error handling,
 * type safety, and performance tracking.
 */
export class TwoFactorClient {
  private client: AxiosInstance;

  /**
   * Create a new 2FA client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config: ApiClientConfig = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add timestamp for performance tracking
        config.metadata = { startTime: Date.now() };

        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
      },
      (error) => {
        return Promise.reject(this.transformError(error));
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        const duration = Date.now() - (response.config.metadata?.startTime || 0);
        response.config.metadata = { ...response.config.metadata, duration };

        trackApiCall({
          endpoint: response.config.url || '',
          method: response.config.method?.toUpperCase() || 'GET',
          duration,
          status: response.status,
          success: true,
          timestamp: Date.now(),
        });

        return response;
      },
      (error) => {
        const duration = Date.now() - (error.config?.metadata?.startTime || 0);

        if (error.config) {
          trackApiCall({
            endpoint: error.config.url || '',
            method: error.config.method?.toUpperCase() || 'GET',
            duration,
            status: error.response?.status || 0,
            success: false,
            timestamp: Date.now(),
            error: error.message,
          });
        }

        return Promise.reject(this.transformError(error));
      }
    );
  }

  /**
   * Transform Axios error to standardized API error
   *
   * @param error - Axios error
   * @returns Transformed API error
   */
  private transformError(error: unknown): ApiError {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;

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
    if (data?.message) {
      return { detail: data.message, status };
    }

    // Default error messages by status code
    const defaultMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      409: 'Conflict. 2FA may already be enabled.',
      422: 'Validation error. Please check your input.',
      500: 'Server error. Please try again later.',
    };

    return {
      detail: defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * Get two-factor authentication status
   *
   * @param userId - User ID to check 2FA status for
   * @returns 2FA status response
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const status = await twoFactorClient.getStatus('user-123');
   * console.log(status.enabled); // true/false
   * console.log(status.method); // 'totp', 'sms', or undefined
   * ```
   */
  async getStatus(userId: string): Promise<TwoFactorStatusResponse> {
    try {
      const response: AxiosResponse<TwoFactorStatusResponse> = await this.client.get(
        '/api/2fa/status',
        { params: { user_id: userId } }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Initiate two-factor authentication setup
   *
   * Generates a TOTP secret and provisioning URI for QR code generation.
   * Also creates backup codes for account recovery.
   *
   * @param request - Setup request with user_id and method
   * @returns Setup response with secret, provisioning URI, and backup codes
   * @throws ApiError if setup fails
   *
   * @example
   * ```ts
   * const setup = await twoFactorClient.setup({
   *   user_id: 'user-123',
   *   method: 'totp',
   * });
   * // Display QR code from setup.provisioning_uri
   * // Save setup.backup_codes securely
   * ```
   */
  async setup(request: TwoFactorSetupRequest): Promise<TwoFactorSetupResponse> {
    try {
      const response: AxiosResponse<TwoFactorSetupResponse> = await this.client.post(
        '/api/2fa/setup',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Verify two-factor authentication code
   *
   * Used to verify the TOTP code during setup or during login.
   * Successful verification during setup enables 2FA for the user.
   *
   * @param request - Verify request with user_id and code
   * @returns Verification response
   * @throws ApiError if verification fails
   *
   * @example
   * ```ts
   * const verify = await twoFactorClient.verify({
   *   user_id: 'user-123',
   *   code: '123456',
   * });
   * if (verify.success) {
   *   console.log('2FA enabled!');
   * }
   * ```
   */
  async verify(request: TwoFactorVerifyRequest): Promise<TwoFactorVerifyResponse> {
    try {
      const response: AxiosResponse<TwoFactorVerifyResponse> = await this.client.post(
        '/api/2fa/verify',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Disable two-factor authentication
   *
   * Requires a valid TOTP code to confirm the disable action.
   * This is a security measure to prevent unauthorized disabling.
   *
   * @param request - Disable request with user_id and confirmation code
   * @returns Success message
   * @throws ApiError if disable fails
   *
   * @example
   * ```ts
   * await twoFactorClient.disable({
   *   user_id: 'user-123',
   *   code: '123456', // Current TOTP code
   * });
   * ```
   */
  async disable(request: TwoFactorDisableRequest): Promise<void> {
    try {
      await this.client.post('/api/2fa/disable', request);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Generate new backup codes
   *
   * Requires a valid TOTP code to verify identity before generating codes.
   * Old backup codes are invalidated when new ones are generated.
   *
   * @param request - Generate request with user_id and verification code
   * @returns New backup codes with security warning
   * @throws ApiError if generation fails
   *
   * @example
   * ```ts
   * const backup = await twoFactorClient.generateBackupCodes({
   *   user_id: 'user-123',
   *   code: '123456', // Current TOTP code
   * });
   * console.log(backup.backup_codes); // Array of 10 codes
   * console.log(backup.warning); // Security warning
   * ```
   */
  async generateBackupCodes(request: BackupCodesGenerateRequest): Promise<BackupCodesResponse> {
    try {
      const response: AxiosResponse<BackupCodesResponse> = await this.client.post(
        '/api/2fa/backup-codes/generate',
        request
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

  /**
   * Get API performance statistics
   *
   * Returns performance metrics for all API calls made through this client.
   *
   * @returns Performance statistics
   */
  getPerformanceStats(): PerformanceStats {
    return getPerformanceStatsUtil();
  }
}

// Extend AxiosRequestConfig to include metadata
declare module 'axios' {
  interface AxiosRequestConfig {
    metadata?: {
      startTime?: number;
      duration?: number;
    };
  }
}

/**
 * Default 2FA client instance
 *
 * Use this singleton instance for all 2FA API calls.
 */
export const twoFactorClient = new TwoFactorClient();

/**
 * Export 2FA client class for custom instances
 */
export default TwoFactorClient;
