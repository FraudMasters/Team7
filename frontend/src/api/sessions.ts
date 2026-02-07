/**
 * Sessions API Client
 *
 * This module provides a typed client for session management operations including
 * listing active sessions, revoking specific sessions, and revoking all sessions.
 *
 * @example
 * ```ts
 * import { sessionsClient } from '@/api/sessions';
 *
 * // List active sessions
 * const sessions = await sessionsClient.listSessions({
 *   user_id: 'user-123',
 *   device_type: 'desktop',
 *   is_active: true,
 * });
 *
 * // Revoke a specific session
 * await sessionsClient.revokeSession('session-123', 'user_logout');
 *
 * // Revoke all sessions for a user
 * const result = await sessionsClient.revokeAllSessions({
 *   user_id: 'user-123',
 *   exclude_current: true,
 *   reason: 'security_reset',
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
  SessionsListResponse,
  RevokeSessionResponse,
  RevokeAllSessionsResponse,
  ApiError,
  ApiClientConfig,
} from '@/types/api';

/**
 * Default sessions API configuration
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 30000, // 30 seconds for session operations
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Sessions API Client class
 *
 * Provides methods for session management with proper error handling,
 * type safety, and performance tracking.
 */
export class SessionsClient {
  private client: AxiosInstance;

  /**
   * Create a new sessions client instance
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
      404: 'Session not found.',
      409: 'Conflict. Session may already be revoked.',
      422: 'Validation error. Please check your input.',
      500: 'Server error. Please try again later.',
    };

    return {
      detail: defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * List active sessions with optional filters
   *
   * Retrieves active user sessions across the system, including device
   * information, IP addresses, and activity timestamps. Sessions are
   * returned in reverse chronological order (most recently active first).
   *
   * @param params - Optional query parameters for filtering
   * @returns Sessions list with total count
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const sessions = await sessionsClient.listSessions({
   *   user_id: 'user-123',
   *   device_type: 'desktop',
   *   is_active: true,
   *   limit: 10,
   *   offset: 0,
   * });
   * console.log(sessions.sessions.length); // Number of sessions
   * console.log(sessions.total_count); // Total count
   * ```
   */
  async listSessions(params?: {
    user_id?: string;
    device_type?: 'desktop' | 'mobile' | 'tablet' | 'unknown';
    is_active?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<SessionsListResponse> {
    try {
      const queryParams: Record<string, string | number | boolean> = {
        limit: params?.limit || 100,
        offset: params?.offset || 0,
      };

      if (params?.user_id) queryParams.user_id = params.user_id;
      if (params?.device_type) queryParams.device_type = params.device_type;
      if (params?.is_active !== undefined) queryParams.is_active = params.is_active;

      const response: AxiosResponse<SessionsListResponse> = await this.client.get(
        '/api/sessions/',
        { params: queryParams }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Revoke a specific session
   *
   * Revokes a specific session by ID, effectively logging out the user
   * from that device. The session is marked as inactive and a revocation
   * timestamp is recorded.
   *
   * @param sessionId - ID of the session to revoke
   * @param reason - Optional reason for revocation (e.g., 'user_logout', 'security_reset')
   * @returns Revoke session response
   * @throws ApiError if revocation fails
   *
   * @example
   * ```ts
   * await sessionsClient.revokeSession('session-123', 'user_logout');
   * // Session is now revoked
   * ```
   */
  async revokeSession(
    sessionId: string,
    reason?: string
  ): Promise<RevokeSessionResponse> {
    try {
      const queryParams: Record<string, string> = {};
      if (reason) queryParams.reason = reason;

      const response: AxiosResponse<RevokeSessionResponse> = await this.client.delete(
        `/api/sessions/${sessionId}`,
        { params: queryParams }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Revoke all sessions for a user
   *
   * Revokes all active sessions for a specific user. This is useful for
   * security purposes, such as when a user changes their password or suspects
   * unauthorized access.
   *
   * By default, the current session (the one making the request) is excluded
   * from revocation to avoid logging out the user who initiated the action.
   *
   * @param params - Revocation parameters
   * @returns Revoke all sessions response with count
   * @throws ApiError if revocation fails
   *
   * @example
   * ```ts
   * const result = await sessionsClient.revokeAllSessions({
   *   user_id: 'user-123',
   *   exclude_current: true,
   *   reason: 'password_change',
   * });
   * console.log(result.revoked_count); // Number of sessions revoked
   * ```
   */
  async revokeAllSessions(params: {
    user_id: string;
    exclude_current?: boolean;
    reason?: string;
  }): Promise<RevokeAllSessionsResponse> {
    try {
      const queryParams: Record<string, string | boolean> = {
        user_id: params.user_id,
        exclude_current: params.exclude_current !== false, // Default to true
      };

      if (params.reason) queryParams.reason = params.reason;

      const response: AxiosResponse<RevokeAllSessionsResponse> = await this.client.delete(
        '/api/sessions/revoke-all',
        { params: queryParams }
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
 * Default sessions client instance
 *
 * Use this singleton instance for all sessions API calls.
 */
export const sessionsClient = new SessionsClient();

/**
 * Export sessions client class for custom instances
 */
export default SessionsClient;
