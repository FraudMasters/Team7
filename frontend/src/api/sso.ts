/**
 * SSO API Client
 *
 * This module provides a typed client for Single Sign-On (SSO) operations including
 * SAML authentication flow, SSO provider configuration, and metadata generation.
 *
 * @example
 * ```ts
 * import { ssoClient } from '@/api/sso';
 *
 * // List SSO providers
 * const providers = await ssoClient.listProviders();
 *
 * // Initiate SAML login
 * const login = await ssoClient.initiateLogin({
 *   provider_id: 'provider-123',
 * });
 * // Redirect user to login.redirect_url
 *
 * // Handle SAML ACS callback
 * const result = await ssoClient.handleACS({
 *   saml_response: samlResponseFromIdP,
 *   provider_id: 'provider-123',
 * });
 *
 * // Create SSO provider configuration
 * const provider = await ssoClient.createProvider({
 *   provider_name: 'Okta',
 *   provider_type: 'okta',
 *   entity_id: 'https://okta.com/entity-id',
 *   sso_url: 'https://okta.com/sso',
 *   x509_certificate: '-----BEGIN CERTIFICATE-----...',
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
  SSOProviderItem,
  SSOProvidersResponse,
  SSOLoginRequest,
  SSOLoginResponse,
  SAMLACSRequest,
  SAMLACSResponse,
  SSOProviderCreate,
  SSOProviderUpdate,
  MetadataResponse,
  ApiError,
  ApiClientConfig,
} from '@/types/api';

/**
 * Default SSO API configuration
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 30000, // 30 seconds for SSO operations
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * SSO API Client class
 *
 * Provides methods for SSO operations with proper error handling,
 * type safety, and performance tracking.
 */
export class SSOClient {
  private client: AxiosInstance;

  /**
   * Create a new SSO client instance
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
      409: 'Resource already exists.',
      422: 'Validation error. Please check your input.',
      500: 'Server error. Please try again later.',
    };

    return {
      detail: defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * List SSO providers with optional filters
   *
   * @param organizationId - Optional organization ID filter
   * @param providerType - Optional provider type filter
   * @param isEnabled - Optional enabled status filter
   * @param limit - Maximum number of providers to return
   * @param offset - Number of providers to skip for pagination
   * @returns List of SSO providers
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const result = await ssoClient.listProviders();
   * console.log(result.providers.length); // Total providers
   * ```
   */
  async listProviders(
    organizationId?: string,
    providerType?: string,
    isEnabled?: boolean,
    limit: number = 100,
    offset: number = 0
  ): Promise<SSOProvidersResponse> {
    try {
      const params: Record<string, string | number | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (providerType) params.provider_type = providerType;
      if (isEnabled !== undefined) params.is_enabled = isEnabled;
      params.limit = limit;
      params.offset = offset;

      const response: AxiosResponse<SSOProvidersResponse> = await this.client.get(
        '/api/sso/providers',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific SSO provider by ID
   *
   * @param providerId - SSO provider ID
   * @returns SSO provider details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const provider = await ssoClient.getProvider('provider-uuid');
   * console.log(provider.provider_name);
   * ```
   */
  async getProvider(providerId: string): Promise<SSOProviderItem> {
    try {
      const response: AxiosResponse<SSOProviderItem> = await this.client.get(
        `/api/sso/providers/${providerId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Initiate SAML login flow
   *
   * Generates a SAML authentication request and returns the IdP redirect URL.
   * The user should be redirected to this URL to complete authentication.
   *
   * @param request - Login request with provider_id and optional relay_state
   * @returns Login response with redirect_url and provider_id
   * @throws ApiError if login initiation fails
   *
   * @example
   * ```ts
   * const login = await ssoClient.initiateLogin({
   *   provider_id: 'provider-123',
   *   relay_state: '/dashboard',
   * });
   * // Redirect user to login.redirect_url
   * window.location.href = login.redirect_url;
   * ```
   */
  async initiateLogin(request: SSOLoginRequest): Promise<SSOLoginResponse> {
    try {
      const response: AxiosResponse<SSOLoginResponse> = await this.client.post(
        '/api/sso/login',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Handle SAML ACS callback
   *
   * Processes the SAML response from the Identity Provider after authentication.
   * Extracts user attributes and returns them for session creation.
   *
   * @param request - ACS request with saml_response and provider_id
   * @returns User attributes extracted from SAML response
   * @throws ApiError if SAML validation fails
   *
   * @example
   * ```ts
   * const result = await ssoClient.handleACS({
   *   saml_response: samlResponseFromIdP,
   *   provider_id: 'provider-123',
   * });
   * console.log(result.email, result.name);
   * ```
   */
  async handleACS(request: SAMLACSRequest): Promise<SAMLACSResponse> {
    try {
      const response: AxiosResponse<SAMLACSResponse> = await this.client.post(
        '/api/sso/acs',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Create SSO provider configuration
   *
   * @param request - Create request with provider details
   * @returns Created SSO provider
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const provider = await ssoClient.createProvider({
   *   provider_name: 'Company Okta',
   *   provider_type: 'okta',
   *   entity_id: 'https://okta.com/entity-id',
   *   sso_url: 'https://okta.com/sso',
   *   x509_certificate: '-----BEGIN CERTIFICATE-----...',
   *   is_enabled: true,
   * });
   * ```
   */
  async createProvider(request: SSOProviderCreate): Promise<SSOProviderItem> {
    try {
      const response: AxiosResponse<SSOProviderItem> = await this.client.post(
        '/api/sso/providers',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update SSO provider configuration
   *
   * @param providerId - SSO provider ID
   * @param request - Update request with fields to modify
   * @returns Updated SSO provider
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await ssoClient.updateProvider('provider-uuid', {
   *   provider_name: 'Updated Company Okta',
   *   is_enabled: false,
   * });
   * ```
   */
  async updateProvider(
    providerId: string,
    request: SSOProviderUpdate
  ): Promise<SSOProviderItem> {
    try {
      const response: AxiosResponse<SSOProviderItem> = await this.client.put(
        `/api/sso/providers/${providerId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete SSO provider configuration
   *
   * @param providerId - SSO provider ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await ssoClient.deleteProvider('provider-uuid');
   * ```
   */
  async deleteProvider(providerId: string): Promise<void> {
    try {
      await this.client.delete(`/api/sso/providers/${providerId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get SAML SP metadata for IdP configuration
   *
   * Returns the Service Provider metadata XML that should be imported
   * into the Identity Provider configuration.
   *
   * @returns XML metadata document
   * @throws ApiError if metadata generation fails
   *
   * @example
   * ```ts
   * const metadata = await ssoClient.getMetadata();
   * console.log(metadata.metadata); // XML string
   * // Download or display for IdP configuration
   * ```
   */
  async getMetadata(): Promise<MetadataResponse> {
    try {
      const response: AxiosResponse<MetadataResponse> = await this.client.get(
        '/api/sso/metadata'
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
 * Default SSO client instance
 *
 * Use this singleton instance for all SSO API calls.
 */
export const ssoClient = new SSOClient();

/**
 * Export SSO client class for custom instances
 */
export default SSOClient;
