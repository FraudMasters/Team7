/**
 * Security Configuration API Client
 *
 * This module provides a typed client for security configuration operations including
 * managing organization security settings, password policies, session management,
 * and IP whitelist management.
 *
 * @example
 * ```ts
 * import { securityConfigClient } from '@/api/securityConfig';
 *
 * // Get security configuration
 * const config = await securityConfigClient.getSecurityConfig('org-123');
 *
 * // Update security settings
 * const updated = await securityConfigClient.updateSecurityConfig('org-123', {
 *   two_factor_required: true,
 *   session_timeout_minutes: 240,
 * });
 *
 * // List IP whitelist entries
 * const whitelist = await securityConfigClient.listIPWhitelist('org-123');
 *
 * // Add IP to whitelist
 * const entry = await securityConfigClient.createIPWhitelistEntry({
 *   organization_id: 'org-123',
 *   name: 'Office Network',
 *   cidr_notation: '192.168.1.0/24',
 *   is_active: true,
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
  SecurityConfigResponse,
  SecurityConfigUpdate,
  SecurityConfigCreate,
  IPWhitelistResponse,
  IPWhitelistItem,
  IPWhitelistCreate,
  IPWhitelistUpdate,
  IPWhitelistDeleteResponse,
  ApiError,
  ApiClientConfig,
} from '@/types/api';

/**
 * Default security config API configuration
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 30000, // 30 seconds for security operations
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Security Configuration API Client class
 *
 * Provides methods for security configuration management with proper error handling,
 * type safety, and performance tracking.
 */
export class SecurityConfigClient {
  private client: AxiosInstance;

  /**
   * Create a new security config client instance
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
      409: 'Conflict. Resource already exists.',
      422: 'Validation error. Please check your input.',
      500: 'Server error. Please try again later.',
    };

    return {
      detail: defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  // ==================== Security Configuration ====================

  /**
   * Get security configuration
   *
   * Retrieves security configuration for an organization or the system default.
   * If an organization_id is provided and no config exists for that organization,
   * the system default configuration is returned.
   *
   * @param organizationId - Optional organization ID (omit for system default)
   * @returns Security configuration
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * // Get system default configuration
   * const config = await securityConfigClient.getSecurityConfig();
   *
   * // Get organization-specific configuration
   * const orgConfig = await securityConfigClient.getSecurityConfig('org-123');
   * ```
   */
  async getSecurityConfig(organizationId?: string): Promise<SecurityConfigResponse> {
    try {
      const params: Record<string, string> = {};
      if (organizationId) params.organization_id = organizationId;

      const response: AxiosResponse<SecurityConfigResponse> = await this.client.get(
        '/api/security/config',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update security configuration
   *
   * Updates security configuration for an organization or the system default.
   * If an organization_id is provided and no config exists for that organization,
   * a new configuration is created based on the system default.
   *
   * @param organizationId - Optional organization ID (omit for system default)
   * @param configUpdate - Security configuration fields to update
   * @returns Updated security configuration
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await securityConfigClient.updateSecurityConfig('org-123', {
   *   two_factor_required: true,
   *   session_timeout_minutes: 240,
   *   ip_whitelist_enabled: true,
   * });
   * ```
   */
  async updateSecurityConfig(
    organizationId: string | undefined,
    configUpdate: SecurityConfigUpdate
  ): Promise<SecurityConfigResponse> {
    try {
      const params: Record<string, string> = {};
      if (organizationId) params.organization_id = organizationId;

      const response: AxiosResponse<SecurityConfigResponse> = await this.client.put(
        '/api/security/config',
        configUpdate,
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Create security configuration for an organization
   *
   * Creates a new security configuration for a specific organization.
   * Only organization-specific configs can be created through this endpoint.
   * System default config is auto-created on first access.
   *
   * @param configCreate - Security configuration to create
   * @returns Created security configuration
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const config = await securityConfigClient.createSecurityConfig({
   *   organization_id: 'org-123',
   *   two_factor_required: true,
   *   session_timeout_minutes: 240,
   *   ip_whitelist_enabled: true,
   * });
   * ```
   */
  async createSecurityConfig(
    configCreate: SecurityConfigCreate
  ): Promise<SecurityConfigResponse> {
    try {
      const response: AxiosResponse<SecurityConfigResponse> = await this.client.post(
        '/api/security/config',
        configCreate
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== IP Whitelist Management ====================

  /**
   * List IP whitelist entries with optional filters
   *
   * Retrieves IP whitelist entries for organizations or system-wide.
   * Entries are returned in reverse chronological order (newest first).
   *
   * @param organizationId - Optional filter for organization ID
   * @param isActive - Optional filter for active status
   * @param limit - Maximum number of entries to return (default: 100, max: 1000)
   * @param offset - Number of entries to skip for pagination (default: 0)
   * @returns IP whitelist entries with total count
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * // Get all active IP whitelist entries for an organization
   * const whitelist = await securityConfigClient.listIPWhitelist('org-123', true);
   *
   * // Get all entries with pagination
   * const page = await securityConfigClient.listIPWhitelist(undefined, undefined, 50, 0);
   * ```
   */
  async listIPWhitelist(
    organizationId?: string,
    isActive?: boolean,
    limit: number = 100,
    offset: number = 0
  ): Promise<IPWhitelistResponse> {
    try {
      const params: Record<string, string | number | boolean> = {
        limit,
        offset,
      };

      if (organizationId) params.organization_id = organizationId;
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<IPWhitelistResponse> = await this.client.get(
        '/api/security/ip-whitelist',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Create IP whitelist entry
   *
   * Creates a new IP whitelist entry for an organization or system-wide.
   * IP whitelist entries enable organizations to restrict access to approved IP addresses or ranges.
   *
   * @param entryCreate - IP whitelist entry to create
   * @returns Created IP whitelist entry
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const entry = await securityConfigClient.createIPWhitelistEntry({
   *   organization_id: 'org-123',
   *   name: 'Office Network',
   *   description: 'Main office IP range',
   *   cidr_notation: '192.168.1.0/24',
   *   is_active: true,
   * });
   * ```
   */
  async createIPWhitelistEntry(entryCreate: IPWhitelistCreate): Promise<IPWhitelistItem> {
    try {
      const response: AxiosResponse<IPWhitelistItem> = await this.client.post(
        '/api/security/ip-whitelist',
        entryCreate
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update IP whitelist entry
   *
   * Updates an existing IP whitelist entry.
   *
   * @param entryId - ID of the IP whitelist entry to update
   * @param entryUpdate - IP whitelist entry fields to update
   * @returns Updated IP whitelist entry
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await securityConfigClient.updateIPWhitelistEntry('whitelist-1', {
   *   name: 'Updated Office Network',
   *   is_active: false,
   * });
   * ```
   */
  async updateIPWhitelistEntry(
    entryId: string,
    entryUpdate: IPWhitelistUpdate
  ): Promise<IPWhitelistItem> {
    try {
      const response: AxiosResponse<IPWhitelistItem> = await this.client.put(
        `/api/security/ip-whitelist/${entryId}`,
        entryUpdate
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete IP whitelist entry
   *
   * Deletes an existing IP whitelist entry.
   *
   * @param entryId - ID of the IP whitelist entry to delete
   * @returns Delete response
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await securityConfigClient.deleteIPWhitelistEntry('whitelist-1');
   * // Entry is now deleted
   * ```
   */
  async deleteIPWhitelistEntry(entryId: string): Promise<IPWhitelistDeleteResponse> {
    try {
      const response: AxiosResponse<IPWhitelistDeleteResponse> = await this.client.delete(
        `/api/security/ip-whitelist/${entryId}`
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
 * Default security config client instance
 *
 * Use this singleton instance for all security config API calls.
 */
export const securityConfigClient = new SecurityConfigClient();

/**
 * Export security config client class for custom instances
 */
export default SecurityConfigClient;
