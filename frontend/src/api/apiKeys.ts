/**
 * API Keys API Client
 *
 * Provides methods for managing API keys used to authenticate
 * requests to the AgentHR developer API.
 *
 * @module api/apiKeys
 */

import { ApiClient } from './client';
import type { ApiError } from '@/types/api';

/**
 * Available API key scopes
 */
export enum APIKeyScope {
  ReadCandidates = 'read:candidates',
  WriteCandidates = 'write:candidates',
  ReadVacancies = 'read:vacancies',
  WriteVacancies = 'write:vacancies',
  ReadResumes = 'read:resumes',
  WriteResumes = 'write:resumes',
  ReadWebhooks = 'read:webhooks',
  WriteWebhooks = 'write:webhooks',
  ReadPlugins = 'read:plugins',
  WritePlugins = 'write:plugins',
  ReadWorkflows = 'read:workflows',
  WriteWorkflows = 'write:workflows',
  ReadAnalytics = 'read:analytics',
}

/**
 * Rate limit configuration
 */
export interface RateLimit {
  requests_per_minute?: number;
  requests_per_hour?: number;
  requests_per_day?: number;
}

/**
 * API key data
 */
export interface APIKey {
  id: string;
  key_prefix: string;
  name: string;
  scopes: string[];
  rate_limit: RateLimit;
  is_active: boolean;
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Generate API key request
 */
export interface GenerateAPIKeyRequest {
  name: string;
  scopes: string[];
  rate_limit?: RateLimit;
  expires_at?: string;
}

/**
 * Generate API key response
 */
export interface GenerateAPIKeyResponse {
  id: string;
  key: string;
  key_prefix: string;
  name: string;
  scopes: string[];
  rate_limit: RateLimit;
  expires_at: string | null;
  created_at: string;
  message: string;
}

/**
 * Revoke API key response
 */
export interface RevokeAPIKeyResponse {
  id: string;
  key_prefix: string;
  name: string;
  is_active: boolean;
  message: string;
}

/**
 * API Keys Client
 *
 * Handles API key management operations.
 */
export class APIKeysClient {
  /**
   * @param apiClient - The API client instance
   */
  constructor(private apiClient: ApiClient) {}

  /**
   * Generate a new API key
   *
   * @param request - API key generation details
   * @returns Generated API key with the full key (only shown once)
   * @throws ApiError if generation fails
   *
   * @example
   * ```ts
   * const result = await apiKeysClient.generateAPIKey({
   *   name: 'Production Integration',
   *   scopes: ['read:candidates', 'read:vacancies']
   * });
   * console.log(result.key); // Save this securely!
   * ```
   */
  async generateAPIKey(request: GenerateAPIKeyRequest): Promise<GenerateAPIKeyResponse> {
    try {
      const response = await this.apiClient.post<GenerateAPIKeyResponse>(
        '/api/api-keys/generate',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List all API keys
   *
   * @param isActive - Optional filter by active status
   * @param skip - Number of records to skip (default: 0)
   * @param limit - Maximum number of records to return (default: 100)
   * @returns List of API keys
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const keys = await apiKeysClient.listAPIKeys();
   * const activeKeys = await apiKeysClient.listAPIKeys(true);
   * ```
   */
  async listAPIKeys(
    isActive?: boolean,
    skip: number = 0,
    limit: number = 100
  ): Promise<APIKey[]> {
    try {
      const params: Record<string, number | boolean> = { skip, limit };
      if (isActive !== undefined) {
        params.is_active = isActive;
      }

      const response = await this.apiClient.getAxiosInstance().get<APIKey[]>(
        '/api/api-keys/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific API key
   *
   * @param keyId - API key UUID
   * @returns API key details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const key = await apiKeysClient.getAPIKey('key-uuid');
   * ```
   */
  async getAPIKey(keyId: string): Promise<APIKey> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<APIKey>(
        `/api/api-keys/${keyId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Revoke an API key
   *
   * @param keyId - API key UUID
   * @returns Revoked API key details
   * @throws ApiError if revocation fails
   *
   * @example
   * ```ts
   * const result = await apiKeysClient.revokeAPIKey('key-uuid');
   * console.log(result.is_active); // false
   * ```
   */
  async revokeAPIKey(keyId: string): Promise<RevokeAPIKeyResponse> {
    try {
      const response = await this.apiClient.post<RevokeAPIKeyResponse>(
        `/api/api-keys/${keyId}/revoke`,
        {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Transform unknown error to ApiError
   */
  private transformError(error: unknown): ApiError {
    if (error && typeof error === 'object' && 'detail' in error) {
      const apiError = error as { detail: string; status?: number };
      return {
        detail: apiError.detail,
        status: apiError.status || 0,
      };
    }
    return {
      detail: error instanceof Error ? error.message : 'An unknown error occurred',
      status: 0,
    };
  }
}

/**
 * Default API keys client instance
 */
export const apiKeysClient = new APIKeysClient(
  new (require('./client').ApiClient)()
);

/**
 * Export API keys client class
 */
export default APIKeysClient;
