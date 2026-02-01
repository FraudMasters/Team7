/**
 * Fairness Monitoring API Client
 *
 * This module provides a convenient interface for monitoring AI model fairness,
 * including retrieving fairness metrics, bias reports, and discrimination alerts.
 *
 * @example
 * ```ts
 * import { fairness } from '@/api/fairness';
 *
 * // Get fairness summary
 * const summary = await fairness.getSummary();
 *
 * // Get fairness metrics
 * const metrics = await fairness.getMetrics({
 *   model_name: 'ranking',
 *   protected_attribute: 'gender',
 * });
 *
 * // Get bias reports
 * const reports = await fairness.getReports({
 *   severity_level: 'high',
 * });
 *
 * // Generate a new bias report
 * const report = await fairness.generateReport({
 *   model_name: 'ranking',
 *   report_type: 'system-wide',
 * });
 *
 * // Acknowledge an alert
 * await fairness.acknowledgeAlert('alert-123');
 * ```
 */

import axios, { AxiosInstance } from 'axios';
import type {
  FairnessMetric,
  FairnessMetricsListResponse,
  BiasReport,
  BiasReportListResponse,
  FairnessAlert,
  FairnessAlertListResponse,
  FairnessSummary,
  GenerateBiasReportRequest,
  AcknowledgeAlertResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 120000,
};

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
 * Fairness Monitoring Client class
 *
 * Provides methods for fairness metrics, bias reports, and alerts.
 */
export class FairnessClient {
  private client: AxiosInstance;

  /**
   * Create a new Fairness client instance
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
   * Get fairness metrics for AI models
   *
   * @param options - Optional filters for metrics
   * @returns Fairness metrics list
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const metrics = await fairness.getMetrics({
   *   model_name: 'ranking',
   *   protected_attribute: 'gender',
   *   metric_type: 'disparate_impact',
   *   is_acceptable: false,
   *   limit: 50,
   * });
   * ```
   */
  async getMetrics(options?: {
    model_name?: string;
    model_version?: string;
    protected_attribute?: string;
    metric_type?: string;
    is_acceptable?: boolean;
    limit?: number;
  }): Promise<FairnessMetricsListResponse> {
    try {
      const params = new URLSearchParams();

      if (options?.model_name) params.append('model_name', options.model_name);
      if (options?.model_version) params.append('model_version', options.model_version);
      if (options?.protected_attribute) params.append('protected_attribute', options.protected_attribute);
      if (options?.metric_type) params.append('metric_type', options.metric_type);
      if (options?.is_acceptable !== undefined) params.append('is_acceptable', String(options.is_acceptable));
      if (options?.limit) params.append('limit', String(options.limit));

      const queryString = params.toString();
      const url = `/api/fairness/metrics${queryString ? `?${queryString}` : ''}`;

      const response = await this.client.get<FairnessMetricsListResponse>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get bias analysis reports
   *
   * @param options - Optional filters for reports
   * @returns Bias reports list
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const reports = await fairness.getReports({
   *   model_name: 'ranking',
   *   severity_level: 'high',
   *   bias_detected: true,
   *   limit: 20,
   * });
   * ```
   */
  async getReports(options?: {
    model_name?: string;
    model_version?: string;
    report_type?: string;
    severity_level?: string;
    bias_detected?: boolean;
    limit?: number;
  }): Promise<BiasReportListResponse> {
    try {
      const params = new URLSearchParams();

      if (options?.model_name) params.append('model_name', options.model_name);
      if (options?.model_version) params.append('model_version', options.model_version);
      if (options?.report_type) params.append('report_type', options.report_type);
      if (options?.severity_level) params.append('severity_level', options.severity_level);
      if (options?.bias_detected !== undefined) params.append('bias_detected', String(options.bias_detected));
      if (options?.limit) params.append('limit', String(options.limit));

      const queryString = params.toString();
      const url = `/api/fairness/reports${queryString ? `?${queryString}` : ''}`;

      const response = await this.client.get<BiasReportListResponse>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get fairness alerts
   *
   * @param options - Optional filters for alerts
   * @returns Fairness alerts list
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const alerts = await fairness.getAlerts({
   *   model_name: 'ranking',
   *   severity: 'high',
   *   acknowledged: false,
   *   days: 7,
   *   limit: 50,
   * });
   * ```
   */
  async getAlerts(options?: {
    model_name?: string;
    alert_type?: string;
    severity?: string;
    acknowledged?: boolean;
    days?: number;
    limit?: number;
  }): Promise<FairnessAlertListResponse> {
    try {
      const params = new URLSearchParams();

      if (options?.model_name) params.append('model_name', options.model_name);
      if (options?.alert_type) params.append('alert_type', options.alert_type);
      if (options?.severity) params.append('severity', options.severity);
      if (options?.acknowledged !== undefined) params.append('acknowledged', String(options.acknowledged));
      if (options?.days) params.append('days', String(options.days));
      if (options?.limit) params.append('limit', String(options.limit));

      const queryString = params.toString();
      const url = `/api/fairness/alerts${queryString ? `?${queryString}` : ''}`;

      const response = await this.client.get<FairnessAlertListResponse>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get fairness summary across all models
   *
   * @returns Fairness summary
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const summary = await fairness.getSummary();
   * console.log(summary.overall_fairness_score);
   * console.log(summary.models_with_issues);
   * ```
   */
  async getSummary(): Promise<FairnessSummary> {
    try {
      const response = await this.client.get<FairnessSummary>('/api/fairness/summary');
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Generate a new bias analysis report
   *
   * @param request - Report generation request
   * @returns Generated bias report
   * @throws ApiError if generation fails
   *
   * @example
   * ```ts
   * const report = await fairness.generateReport({
   *   model_name: 'ranking',
   *   model_version: 'v1.0.0',
   *   report_type: 'system-wide',
   * });
   * ```
   */
  async generateReport(request: GenerateBiasReportRequest): Promise<BiasReport> {
    try {
      const params = new URLSearchParams();
      params.append('model_name', request.model_name);
      if (request.model_version) params.append('model_version', request.model_version);
      if (request.report_type) params.append('report_type', request.report_type);

      const response = await this.client.post<BiasReport>(
        `/api/fairness/reports/generate?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Acknowledge a fairness alert
   *
   * @param alertId - ID of the alert to acknowledge
   * @returns Acknowledgment response
   * @throws ApiError if acknowledgment fails
   *
   * @example
   * ```ts
   * const result = await fairness.acknowledgeAlert('alert-123');
   * console.log(result.acknowledged); // true
   * ```
   */
  async acknowledgeAlert(alertId: string): Promise<AcknowledgeAlertResponse> {
    try {
      const response = await this.client.post<AcknowledgeAlertResponse>(
        `/api/fairness/alerts/${alertId}/acknowledge`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get a specific bias report by ID
   *
   * @param reportId - Report ID
   * @returns Bias report details
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const report = await fairness.getReport('report-123');
   * ```
   */
  async getReport(reportId: string): Promise<BiasReport> {
    try {
      const response = await this.client.get<BiasReport>(`/api/fairness/reports/${reportId}`);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get fairness metrics for a specific model
   *
   * @param modelName - Model name
   * @param options - Optional filters
   * @returns Fairness metrics for the model
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const metrics = await fairness.getModelMetrics('ranking', {
   *   protected_attribute: 'gender',
   * });
   * ```
   */
  async getModelMetrics(
    modelName: string,
    options?: {
      model_version?: string;
      protected_attribute?: string;
      metric_type?: string;
      limit?: number;
    }
  ): Promise<FairnessMetricsListResponse> {
    return this.getMetrics({
      model_name: modelName,
      ...options,
    });
  }

  /**
   * Get alerts for a specific model
   *
   * @param modelName - Model name
   * @param options - Optional filters
   * @returns Alerts for the model
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const alerts = await fairness.getModelAlerts('ranking', {
   *   severity: 'high',
   *   acknowledged: false,
   * });
   * ```
   */
  async getModelAlerts(
    modelName: string,
    options?: {
      alert_type?: string;
      severity?: string;
      acknowledged?: boolean;
      days?: number;
      limit?: number;
    }
  ): Promise<FairnessAlertListResponse> {
    return this.getAlerts({
      model_name: modelName,
      ...options,
    });
  }

  /**
   * Get critical unacknowledged alerts
   *
   * Convenience method for getting high-priority alerts that need attention.
   *
   * @returns Critical alerts
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const criticalAlerts = await fairness.getCriticalAlerts();
   * ```
   */
  async getCriticalAlerts(): Promise<FairnessAlertListResponse> {
    return this.getAlerts({
      severity: 'critical',
      acknowledged: false,
      days: 7,
      limit: 100,
    });
  }
}

/**
 * Default fairness client instance
 *
 * Use this singleton instance for all fairness API calls.
 */
export const fairness = new FairnessClient();

/**
 * Export fairness client class for custom instances
 */
export default FairnessClient;
