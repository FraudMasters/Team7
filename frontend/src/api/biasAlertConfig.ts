/**
 * Bias Alert Configuration API Client
 *
 * This module provides a convenient interface for managing bias alert configurations,
 * including creating, retrieving, updating, and deleting alert threshold settings.
 *
 * @example
 * ```ts
 * import { biasAlertConfig } from '@/api/biasAlertConfig';
 *
 * // Get all configurations
 * const configs = await biasAlertConfig.getConfigs();
 *
 * // Get configurations for specific organization
 * const orgConfigs = await biasAlertConfig.getConfigs({
 *   organization_id: 'org-123',
 *   is_enabled: true,
 * });
 *
 * // Create a new configuration
 * const newConfig = await biasAlertConfig.createConfig({
 *   alert_type: 'disparate_impact',
 *   metric_name: 'Gender Disparate Impact',
 *   threshold_value: 0.8,
 *   severity_level: 'high',
 * });
 *
 * // Update a configuration
 * const updated = await biasAlertConfig.updateConfig('config-123', {
 *   threshold_value: 0.75,
 *   is_enabled: false,
 * });
 *
 * // Delete a configuration
 * await biasAlertConfig.deleteConfig('config-123');
 * ```
 */

import axios, { AxiosInstance } from 'axios';
import { config } from '@/config';

/**
 * Default API configuration
 */
const DEFAULT_CONFIG = {
  baseURL: config.api.url,
  timeout: 30000,
};

/**
 * API Error type
 */
export interface ApiError {
  detail: string;
  status?: number;
}

/**
 * Bias Alert Configuration interface
 */
export interface BiasAlertConfig {
  id: string;
  organization_id?: string | null;
  alert_type: string;
  metric_name: string;
  threshold_value: number;
  comparison_operator: string;
  severity_level: string;
  is_enabled: boolean;
  notification_enabled: boolean;
  notification_recipients?: string[] | null;
  demographic_groups?: string[] | null;
  applies_to_vacancies?: string[] | null;
  alert_frequency: string;
  cooldown_period_hours?: number | null;
  auto_acknowledge: boolean;
  description?: string | null;
  mitigation_recommendations?: string | null;
  custom_message_template?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

/**
 * Request model for creating a new bias alert configuration
 */
export interface BiasAlertConfigCreate {
  organization_id?: string | null;
  alert_type: string;
  metric_name: string;
  threshold_value: number;
  comparison_operator?: string;
  severity_level?: string;
  is_enabled?: boolean;
  notification_enabled?: boolean;
  notification_recipients?: string[] | null;
  demographic_groups?: string[] | null;
  applies_to_vacancies?: string[] | null;
  alert_frequency?: string;
  cooldown_period_hours?: number | null;
  auto_acknowledge?: boolean;
  description?: string | null;
  mitigation_recommendations?: string | null;
  custom_message_template?: string | null;
  metadata?: Record<string, unknown> | null;
}

/**
 * Request model for updating an existing bias alert configuration
 */
export interface BiasAlertConfigUpdate {
  alert_type?: string;
  metric_name?: string;
  threshold_value?: number;
  comparison_operator?: string;
  severity_level?: string;
  is_enabled?: boolean;
  notification_enabled?: boolean;
  notification_recipients?: string[] | null;
  demographic_groups?: string[] | null;
  applies_to_vacancies?: string[] | null;
  alert_frequency?: string;
  cooldown_period_hours?: number | null;
  auto_acknowledge?: boolean;
  description?: string | null;
  mitigation_recommendations?: string | null;
  custom_message_template?: string | null;
  metadata?: Record<string, unknown> | null;
}

/**
 * Response model for list of bias alert configurations
 */
export interface BiasAlertConfigListResponse {
  configs: BiasAlertConfig[];
  total_count: number;
}

/**
 * Transform Axios error to standardized API error
 */
function transformError(error: unknown): ApiError {
  const axiosError = error as {
    response?: { status?: number; data?: { detail?: string } };
    message?: string;
  };

  return {
    detail: axiosError.response?.data?.detail ?? axiosError.message ?? 'Unknown error',
    status: axiosError.response?.status,
  };
}

/**
 * Bias Alert Configuration Client class
 *
 * Provides methods for managing bias alert configurations.
 */
export class BiasAlertConfigClient {
  private client: AxiosInstance;

  /**
   * Create a new Bias Alert Configuration client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);
  }

  /**
   * Get the underlying axios instance for custom requests
   *
   * @returns Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }

  /**
   * Get list of bias alert configurations
   *
   * @param options - Optional filters for configurations
   * @returns Bias alert configurations list
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const configs = await biasAlertConfig.getConfigs({
   *   organization_id: 'org-123',
   *   alert_type: 'disparate_impact',
   *   is_enabled: true,
   *   limit: 50,
   * });
   * ```
   */
  async getConfigs(options?: {
    organization_id?: string;
    alert_type?: string;
    is_enabled?: boolean;
    limit?: number;
  }): Promise<BiasAlertConfigListResponse> {
    try {
      const params = new URLSearchParams();

      if (options?.organization_id) params.append('organization_id', options.organization_id);
      if (options?.alert_type) params.append('alert_type', options.alert_type);
      if (options?.is_enabled !== undefined) params.append('is_enabled', String(options.is_enabled));
      if (options?.limit) params.append('limit', String(options.limit));

      const queryString = params.toString();
      const url = `/api/bias-alert-config${queryString ? `?${queryString}` : ''}`;

      const response = await this.client.get<BiasAlertConfigListResponse>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get a specific bias alert configuration by ID
   *
   * @param configId - Configuration ID
   * @returns Bias alert configuration
   * @throws ApiError if fetch fails or configuration not found
   *
   * @example
   * ```ts
   * const config = await biasAlertConfig.getConfig('config-123');
   * ```
   */
  async getConfig(configId: string): Promise<BiasAlertConfig> {
    try {
      const response = await this.client.get<BiasAlertConfig>(
        `/api/bias-alert-config/${configId}`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Create a new bias alert configuration
   *
   * @param configData - Configuration data for the new alert
   * @returns Created bias alert configuration
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const newConfig = await biasAlertConfig.createConfig({
   *   alert_type: 'disparate_impact',
   *   metric_name: 'Gender Disparate Impact',
   *   threshold_value: 0.8,
   *   severity_level: 'high',
   *   notification_enabled: true,
   *   notification_recipients: ['admin@example.com'],
   * });
   * ```
   */
  async createConfig(configData: BiasAlertConfigCreate): Promise<BiasAlertConfig> {
    try {
      const response = await this.client.post<BiasAlertConfig>(
        '/api/bias-alert-config',
        configData
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Update an existing bias alert configuration
   *
   * @param configId - Configuration ID
   * @param configData - Updated configuration data
   * @returns Updated bias alert configuration
   * @throws ApiError if update fails or configuration not found
   *
   * @example
   * ```ts
   * const updated = await biasAlertConfig.updateConfig('config-123', {
   *   threshold_value: 0.75,
   *   is_enabled: false,
   * });
   * ```
   */
  async updateConfig(
    configId: string,
    configData: BiasAlertConfigUpdate
  ): Promise<BiasAlertConfig> {
    try {
      const response = await this.client.put<BiasAlertConfig>(
        `/api/bias-alert-config/${configId}`,
        configData
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Delete a bias alert configuration
   *
   * @param configId - Configuration ID
   * @throws ApiError if deletion fails or configuration not found
   *
   * @example
   * ```ts
   * await biasAlertConfig.deleteConfig('config-123');
   * ```
   */
  async deleteConfig(configId: string): Promise<void> {
    try {
      await this.client.delete(`/api/bias-alert-config/${configId}`);
    } catch (error) {
      throw transformError(error);
    }
  }
}

/**
 * Default bias alert configuration client instance
 */
export const biasAlertConfig = new BiasAlertConfigClient();
