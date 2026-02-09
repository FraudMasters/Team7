/**
 * Bias Reports API Client
 *
 * This module provides a focused interface for bias report operations,
 * including generating reports, retrieving report details, and exporting reports.
 *
 * @example
 * ```ts
 * import { biasReports } from '@/api/biasReports';
 *
 * // List bias reports
 * const reports = await biasReports.getReports({
 *   severity_level: 'high',
 *   limit: 20,
 * });
 *
 * // Get a specific report
 * const report = await biasReports.getReport('2024-01-25_v1.0');
 *
 * // Generate a new bias report
 * const newReport = await biasReports.generateReport({
 *   model_name: 'ranking',
 *   report_type: 'system-wide',
 * });
 *
 * // Export a report as PDF
 * const blob = await biasReports.exportReport('2024-01-25_v1.0', 'pdf');
 * ```
 */

import axios, { AxiosInstance } from 'axios';
import { config } from '@/config';
import type {
  BiasReport,
  BiasReportListResponse,
  GenerateBiasReportRequest,
  FairnessScorecard,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration
 */
const DEFAULT_CONFIG = {
  baseURL: config.api.url,
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
 * Bias Reports Client class
 *
 * Provides methods for bias report operations.
 */
export class BiasReportsClient {
  private client: AxiosInstance;

  /**
   * Create a new BiasReports client instance
   *
   * @param configOverride - Optional configuration overrides
   */
  constructor(configOverride = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...configOverride };

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
   * Get bias analysis reports
   *
   * @param options - Optional filters for reports
   * @returns Bias reports list
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const reports = await biasReports.getReports({
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
      if (options?.bias_detected !== undefined) {
        params.append('bias_detected', String(options.bias_detected));
      }
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
   * Get a specific bias report by ID
   *
   * @param reportId - Report ID (format: {analysis_date}_{model_version})
   * @returns Bias report details
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const report = await biasReports.getReport('2024-01-25_v1.0');
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
   * Generate a new bias analysis report
   *
   * @param request - Report generation request
   * @returns Generated bias report
   * @throws ApiError if generation fails
   *
   * @example
   * ```ts
   * const report = await biasReports.generateReport({
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
   * Get fairness scorecard for a vacancy or model version
   *
   * @param options - Optional filters for scorecard
   * @returns Fairness scorecard data
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const scorecard = await biasReports.getScorecard({
   *   vacancy_id: 'vacancy-123',
   * });
   * ```
   */
  async getScorecard(options?: {
    vacancy_id?: string;
    model_version?: string;
  }): Promise<FairnessScorecard> {
    try {
      const params = new URLSearchParams();

      if (options?.vacancy_id) params.append('vacancy_id', options.vacancy_id);
      if (options?.model_version) params.append('model_version', options.model_version);

      const queryString = params.toString();
      const url = `/api/fairness/scorecard${queryString ? `?${queryString}` : ''}`;

      const response = await this.client.get<FairnessScorecard>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Export a bias report in PDF or CSV format
   *
   * @param reportId - Report ID to export
   * @param format - Export format ('pdf' or 'csv')
   * @returns Blob containing the exported file data
   * @throws ApiError if export fails
   *
   * @example
   * ```ts
   * const blob = await biasReports.exportReport('2024-01-25_v1.0', 'pdf');
   * // Create download link
   * const url = URL.createObjectURL(blob);
   * const link = document.createElement('a');
   * link.href = url;
   * link.download = 'bias_report.pdf';
   * link.click();
   * ```
   */
  async exportReport(reportId: string, format: 'pdf' | 'csv' = 'pdf'): Promise<Blob> {
    try {
      const response = await this.client.post(
        `/api/fairness/reports/${reportId}/export?format=${format}`,
        undefined,
        {
          responseType: 'blob',
        }
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get reports for a specific model
   *
   * @param modelName - Model name
   * @param options - Optional filters
   * @returns Reports for the model
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const reports = await biasReports.getModelReports('ranking', {
   *   severity_level: 'high',
   * });
   * ```
   */
  async getModelReports(
    modelName: string,
    options?: {
      model_version?: string;
      report_type?: string;
      severity_level?: string;
      bias_detected?: boolean;
      limit?: number;
    }
  ): Promise<BiasReportListResponse> {
    return this.getReports({
      model_name: modelName,
      ...options,
    });
  }

  /**
   * Get critical severity reports
   *
   * Convenience method for getting high-severity bias reports.
   *
   * @returns Critical reports
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const criticalReports = await biasReports.getCriticalReports();
   * ```
   */
  async getCriticalReports(): Promise<BiasReportListResponse> {
    return this.getReports({
      severity_level: 'critical',
      bias_detected: true,
      limit: 100,
    });
  }

  /**
   * Get recent reports (last 7 days)
   *
   * @param options - Optional filters
   * @returns Recent reports
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const recentReports = await biasReports.getRecentReports({
   *   limit: 20,
   * });
   * ```
   */
  async getRecentReports(options?: { limit?: number }): Promise<BiasReportListResponse> {
    return this.getReports({
      limit: options?.limit ?? 20,
    });
  }
}

/**
 * Default bias reports client instance
 *
 * Use this singleton instance for all bias reports API calls.
 */
export const biasReports = new BiasReportsClient();

/**
 * Export bias reports client class for custom instances
 */
export default BiasReportsClient;
