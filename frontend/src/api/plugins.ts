/**
 * Plugins API Client
 *
 * Provides methods for managing plugins in the AgentHR marketplace.
 *
 * @module api/plugins
 */

import { ApiClient } from './client';
import type { ApiError } from '@/types/api';

/**
 * Plugin category enum
 */
export enum PluginCategory {
  Integration = 'integration',
  Analytics = 'analytics',
  Automation = 'automation',
  Notification = 'notification',
  Export = 'export',
  Import = 'import',
  Workflow = 'workflow',
  CustomUI = 'custom_ui',
  DataSource = 'data_source',
  AIEnhancement = 'ai_enhancement',
  Other = 'other',
}

/**
 * Plugin status enum
 */
export enum PluginStatus {
  Draft = 'draft',
  PendingReview = 'pending_review',
  Approved = 'approved',
  Rejected = 'rejected',
  Deprecated = 'deprecated',
  Archived = 'archived',
}

/**
 * Plugin data (list item)
 */
export interface Plugin {
  id: string;
  name: string;
  slug: string;
  version: string;
  author: string;
  description: string;
  category: string;
  tags: string[];
  logo_url: string | null;
  is_official: boolean;
  status: string;
  is_active: boolean;
  install_count: number;
  rating_count: number;
  average_rating: number | null;
  is_installed: boolean;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Plugin detail data
 */
export interface PluginDetail extends Plugin {
  long_description: string | null;
  homepage_url: string | null;
  repository_url: string | null;
  documentation_url: string | null;
  manifest_url: string;
  download_url: string;
  latest_version: string | null;
  min_agenthr_version: string | null;
  max_agenthr_version: string | null;
  permissions: string[];
  dependencies: Record<string, unknown> | null;
  is_compatible: boolean;
  config_schema: Record<string, unknown> | null;
  license: string | null;
}

/**
 * Plugin installation data
 */
export interface PluginInstallation {
  id: string;
  plugin_id: string;
  plugin_name: string;
  plugin_slug: string;
  plugin_version: string;
  version: string;
  description: string;
  category: string;
  logo_url: string | null;
  is_enabled: boolean;
  config: Record<string, unknown> | null;
  install_notes: string | null;
  installed_at: string;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * List plugins request filters
 */
export interface ListPluginsFilters {
  category?: string;
  is_official?: boolean;
  is_active?: boolean;
  status?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

/**
 * Install plugin request
 */
export interface InstallPluginRequest {
  version?: string;
  config?: Record<string, unknown>;
  install_notes?: string;
}

/**
 * Install plugin response
 */
export interface InstallPluginResponse {
  id: string;
  plugin_id: string;
  plugin_name: string;
  version: string;
  is_enabled: boolean;
  message: string;
}

/**
 * Uninstall plugin response
 */
export interface UninstallPluginResponse {
  id: string;
  plugin_id: string;
  message: string;
}

/**
 * Update plugin installation request
 */
export interface UpdatePluginInstallationRequest {
  is_enabled?: boolean;
  config?: Record<string, unknown>;
  install_notes?: string;
}

/**
 * Update plugin installation response
 */
export interface UpdatePluginInstallationResponse {
  id: string;
  plugin_id: string;
  plugin_name: string;
  is_enabled: boolean;
  config: Record<string, unknown> | null;
  install_notes: string | null;
  message: string;
}

/**
 * Marketplace statistics
 */
export interface MarketplaceStatistics {
  total_plugins: number;
  official_plugins: number;
  community_plugins: number;
  total_installations: number;
  categories: Record<string, number>;
}

/**
 * Plugins Client
 *
 * Handles plugin marketplace and installation management operations.
 */
export class PluginsClient {
  /**
   * @param apiClient - The API client instance
   */
  constructor(private apiClient: ApiClient) {}

  /**
   * List all available plugins in the marketplace
   *
   * @param filters - Optional filters for listing plugins
   * @returns List of plugins
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const plugins = await pluginsClient.listPlugins({ category: 'integration' });
   * const searchResults = await pluginsClient.listPlugins({ search: 'slack' });
   * ```
   */
  async listPlugins(filters?: ListPluginsFilters): Promise<Plugin[]> {
    try {
      const params: Record<string, string | number | boolean> = {};
      if (filters) {
        if (filters.category) params.category = filters.category;
        if (filters.is_official !== undefined) params.is_official = filters.is_official;
        if (filters.is_active !== undefined) params.is_active = filters.is_active;
        if (filters.status) params.status = filters.status;
        if (filters.search) params.search = filters.search;
        params.skip = filters.skip ?? 0;
        params.limit = filters.limit ?? 100;
      }

      const response = await this.apiClient.getAxiosInstance().get<Plugin[]>(
        '/api/plugins/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get detailed information about a specific plugin
   *
   * @param pluginId - Plugin UUID
   * @returns Plugin details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const plugin = await pluginsClient.getPlugin('plugin-uuid');
   * ```
   */
  async getPlugin(pluginId: string): Promise<PluginDetail> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<PluginDetail>(
        `/api/plugins/${pluginId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Install a plugin for the current user
   *
   * @param pluginId - Plugin UUID
   * @param request - Installation options
   * @returns Installation details
   * @throws ApiError if installation fails
   *
   * @example
   * ```ts
   * const result = await pluginsClient.installPlugin('plugin-uuid', {
   *   config: { api_key: 'xxx' }
   * });
   * ```
   */
  async installPlugin(pluginId: string, request?: InstallPluginRequest): Promise<InstallPluginResponse> {
    try {
      const response = await this.apiClient.post<InstallPluginResponse>(
        `/api/plugins/${pluginId}/install`,
        request ?? {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Uninstall a plugin
   *
   * @param pluginId - Plugin UUID
   * @returns Uninstall confirmation
   * @throws ApiError if uninstallation fails
   *
   * @example
   * ```ts
   * const result = await pluginsClient.uninstallPlugin('plugin-uuid');
   * ```
   */
  async uninstallPlugin(pluginId: string): Promise<UninstallPluginResponse> {
    try {
      const response = await this.apiClient.post<UninstallPluginResponse>(
        `/api/plugins/${pluginId}/uninstall`,
        {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List installed plugins
   *
   * @param isEnabled - Optional filter by enabled status
   * @param skip - Number of records to skip (default: 0)
   * @param limit - Maximum number of records to return (default: 100)
   * @returns List of installed plugins
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const installed = await pluginsClient.listInstalled();
   * const enabled = await pluginsClient.listInstalled(true);
   * ```
   */
  async listInstalled(isEnabled?: boolean, skip: number = 0, limit: number = 100): Promise<PluginInstallation[]> {
    try {
      const params: Record<string, number | boolean> = { skip, limit };
      if (isEnabled !== undefined) {
        params.is_enabled = isEnabled;
      }

      const response = await this.apiClient.getAxiosInstance().get<PluginInstallation[]>(
        '/api/plugins/installed/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a plugin installation (enable/disable, configure)
   *
   * @param installationId - Installation UUID
   * @param request - Update options
   * @returns Updated installation details
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const result = await pluginsClient.updateInstallation('install-uuid', {
   *   is_enabled: false
   * });
   * ```
   */
  async updateInstallation(
    installationId: string,
    request: UpdatePluginInstallationRequest
  ): Promise<UpdatePluginInstallationResponse> {
    try {
      const response = await this.apiClient.put<UpdatePluginInstallationResponse>(
        `/api/plugins/installed/${installationId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get marketplace statistics
   *
   * @returns Marketplace statistics
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const stats = await pluginsClient.getMarketplaceStats();
   * console.log(stats.total_plugins);
   * ```
   */
  async getMarketplaceStats(): Promise<MarketplaceStatistics> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<MarketplaceStatistics>(
        '/api/plugins/statistics/marketplace'
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
 * Default plugins client instance
 */
export const pluginsClient = new PluginsClient(
  new (require('./client').ApiClient)()
);

/**
 * Export plugins client class
 */
export default PluginsClient;
