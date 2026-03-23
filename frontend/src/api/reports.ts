/**
 * Reports API Client
 *
 * Provides methods for managing custom analytics reports, scheduled reports,
 * and report generation/export functionality including PDF, Excel, and CSV formats.
 *
 * @module api/reports
 */

import { ApiClient } from './client';
import type { ApiError } from '@/types/api';

/**
 * Report types available in the system
 */
export enum ReportType {
  CandidateSummary = 'candidate_summary',
  HiringPipeline = 'hiring_pipeline',
  EEOCCompliance = 'eeoc_compliance',
  CustomAnalytics = 'custom_analytics',
  RecruiterPerformance = 'recruiter_performance',
  SourceEffectiveness = 'source_effectiveness',
}

/**
 * Supported export formats for reports
 */
export enum ReportFormat {
  PDF = 'pdf',
  Excel = 'excel',
  CSV = 'csv',
}

/**
 * Frequency options for scheduled reports
 */
export enum ReportScheduleFrequency {
  Daily = 'daily',
  Weekly = 'weekly',
  Monthly = 'monthly',
}

/**
 * Request model for creating a custom report
 */
export interface ReportCreate {
  organization_id: string;
  name: string;
  description?: string;
  report_type: ReportType;
  configuration: Record<string, any>;
  created_by?: string;
  is_active?: boolean;
}

/**
 * Request model for updating a custom report
 */
export interface ReportUpdate {
  name?: string;
  description?: string;
  report_type?: ReportType;
  configuration?: Record<string, any>;
  is_active?: boolean;
}

/**
 * Response model for a single report entry
 */
export interface ReportResponse {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  report_type: string;
  configuration: Record<string, any>;
  created_by?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Response model for listing reports
 */
export interface ReportListResponse {
  reports: ReportResponse[];
  total_count: number;
  organization_id?: string;
}

/**
 * Request model for creating a scheduled report
 */
export interface ScheduledReportCreate {
  organization_id: string;
  report_id: string;
  name: string;
  schedule_config: ScheduleConfig;
  delivery_config: DeliveryConfig;
  recipients: string[];
  created_by?: string;
  is_active?: boolean;
}

/**
 * Request model for updating a scheduled report
 */
export interface ScheduledReportUpdate {
  name?: string;
  schedule_config?: ScheduleConfig;
  delivery_config?: DeliveryConfig;
  recipients?: string[];
  is_active?: boolean;
}

/**
 * Response model for a scheduled report entry
 */
export interface ScheduledReportResponse {
  id: string;
  organization_id: string;
  report_id: string;
  name: string;
  schedule_config: ScheduleConfig;
  delivery_config: DeliveryConfig;
  recipients: string[];
  created_by?: string;
  is_active: boolean;
  next_run_at?: string;
  last_run_at?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Response model for listing scheduled reports
 */
export interface ScheduledReportListResponse {
  scheduled_reports: ScheduledReportResponse[];
  total_count: number;
  organization_id?: string;
}

/**
 * Request model for generating a report on-demand
 */
export interface ReportGenerationRequest {
  report_id: string;
  format?: ReportFormat;
  override_filters?: Record<string, any>;
}

/**
 * Response model for report generation result
 */
export interface ReportGenerationResponse {
  report_id: string;
  format: string;
  download_url: string;
  expires_at: string;
  generated_at: string;
  file_size_bytes?: number;
}

/**
 * Audit log entry for report access
 */
export interface ReportAuditLogEntry {
  report_id: string;
  user_id: string;
  action: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

/**
 * Configuration for scheduled report execution
 */
export interface ScheduleConfig {
  frequency: ReportScheduleFrequency;
  hour: number;
  minute?: number;
  day_of_week?: number;
  day_of_month?: number;
  timezone?: string;
}

/**
 * Configuration for report delivery
 */
export interface DeliveryConfig {
  format: ReportFormat;
  include_charts?: boolean;
  include_summary?: boolean;
  email_subject?: string;
  email_body?: string;
}

/**
 * Request model for exporting a report to PDF
 */
export interface PDFExportRequest {
  report_id: string;
  data: Record<string, any>;
  format?: string;
}

/**
 * Response model for PDF export
 */
export interface PDFExportResponse {
  report_id: string;
  download_url: string;
  expires_at: string;
}

/**
 * Request model for exporting analytics data to CSV
 */
export interface CSVExportRequest {
  metrics: string[];
  filters?: Record<string, any>;
  include_headers?: boolean;
}

/**
 * Response model for CSV export
 */
export interface CSVExportResponse {
  download_url: string;
  expires_at: string;
  row_count: number;
}

/**
 * Reports API Client class
 *
 * Provides methods for managing custom reports, scheduled reports,
 * and report generation/export functionality.
 */
export class ReportsClient {
  /**
   * @param apiClient - The API client instance
   */
  constructor(private apiClient: ApiClient) {}

  // ==================== Report Management ====================

  /**
   * Create a new custom report
   *
   * @param data - Report creation data
   * @returns Created report details
   * @throws {ApiError} If the request fails
   */
  async createReport(data: ReportCreate): Promise<ReportResponse> {
    try {
      const response = await this.apiClient.getAxiosInstance().post<ReportResponse>(
        '/api/reports/',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List custom reports with optional filtering
   *
   * @param organizationId - Optional organization ID filter
   * @param createdBy - Optional creator user ID filter
   * @returns List of reports with metadata
   * @throws {ApiError} If the request fails
   */
  async listReports(
    organizationId?: string,
    createdBy?: string
  ): Promise<ReportListResponse> {
    try {
      const params: Record<string, string> = {};
      if (organizationId) params.organization_id = organizationId;
      if (createdBy) params.created_by = createdBy;

      const response = await this.apiClient.getAxiosInstance().get<ReportListResponse>(
        '/api/reports/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific report by ID
   *
   * @param reportId - Report identifier
   * @returns Report details
   * @throws {ApiError} If the request fails
   */
  async getReport(reportId: string): Promise<ReportResponse> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<ReportResponse>(
        `/api/reports/${reportId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update an existing report
   *
   * @param reportId - Report identifier
   * @param data - Report update data
   * @returns Updated report details
   * @throws {ApiError} If the request fails
   */
  async updateReport(reportId: string, data: ReportUpdate): Promise<ReportResponse> {
    try {
      const response = await this.apiClient.getAxiosInstance().put<ReportResponse>(
        `/api/reports/${reportId}`,
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a report
   *
   * @param reportId - Report identifier
   * @throws {ApiError} If the request fails
   */
  async deleteReport(reportId: string): Promise<void> {
    try {
      await this.apiClient.getAxiosInstance().delete(`/api/reports/${reportId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete all reports for a specific organization
   *
   * @param organizationId - Organization identifier
   * @throws {ApiError} If the request fails
   */
  async deleteReportsByOrganization(organizationId: string): Promise<void> {
    try {
      await this.apiClient.getAxiosInstance().delete(
        `/api/reports/organization/${organizationId}`
      );
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Report Generation & Export ====================

  /**
   * Export a report to PDF format
   *
   * @param request - PDF export request details
   * @returns PDF download URL and metadata
   * @throws {ApiError} If the request fails
   */
  async exportReportPDF(request: PDFExportRequest): Promise<PDFExportResponse> {
    try {
      const response = await this.apiClient.getAxiosInstance().post<PDFExportResponse>(
        '/api/reports/export/pdf',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Export analytics data to CSV format
   *
   * @param request - CSV export request details
   * @returns CSV download URL and metadata
   * @throws {ApiError} If the request fails
   */
  async exportReportCSV(request: CSVExportRequest): Promise<CSVExportResponse> {
    try {
      const response = await this.apiClient.getAxiosInstance().post<CSVExportResponse>(
        '/api/reports/export/csv',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Generate a report on-demand with specified format
   *
   * @param request - Report generation request
   * @returns Generated report download URL and metadata
   * @throws {ApiError} If the request fails
   */
  async generateReport(request: ReportGenerationRequest): Promise<ReportGenerationResponse> {
    try {
      const format = request.format || ReportFormat.PDF;
      const endpoint = format === ReportFormat.PDF
        ? '/api/reports/export/pdf'
        : '/api/reports/export/csv';

      let requestData: any;
      if (format === ReportFormat.PDF) {
        requestData = {
          report_id: request.report_id,
          data: request.override_filters || {},
          format: 'A4',
        };
      } else {
        requestData = {
          metrics: [],
          filters: request.override_filters || {},
          include_headers: true,
        };
      }

      const response = await this.apiClient.getAxiosInstance().post<ReportGenerationResponse>(
        endpoint,
        requestData
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Scheduled Reports ====================

  /**
   * Create a new scheduled report
   *
   * @param data - Scheduled report creation data
   * @returns Created scheduled report details
   * @throws {ApiError} If the request fails
   */
  async createScheduledReport(data: ScheduledReportCreate): Promise<ScheduledReportResponse> {
    try {
      const response = await this.apiClient.getAxiosInstance().post<ScheduledReportResponse>(
        '/api/reports/schedule',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List scheduled reports with optional filtering
   *
   * @param organizationId - Optional organization ID filter
   * @returns List of scheduled reports
   * @throws {ApiError} If the request fails
   */
  async listScheduledReports(organizationId?: string): Promise<ScheduledReportListResponse> {
    try {
      const params: Record<string, string> = {};
      if (organizationId) params.organization_id = organizationId;

      const response = await this.apiClient.getAxiosInstance().get<ScheduledReportListResponse>(
        '/api/reports/schedules/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific scheduled report by ID
   *
   * @param scheduleId - Scheduled report identifier
   * @returns Scheduled report details
   * @throws {ApiError} If the request fails
   */
  async getScheduledReport(scheduleId: string): Promise<ScheduledReportResponse> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<ScheduledReportResponse>(
        `/api/reports/schedules/${scheduleId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update an existing scheduled report
   *
   * @param scheduleId - Scheduled report identifier
   * @param data - Scheduled report update data
   * @returns Updated scheduled report details
   * @throws {ApiError} If the request fails
   */
  async updateScheduledReport(
    scheduleId: string,
    data: ScheduledReportUpdate
  ): Promise<ScheduledReportResponse> {
    try {
      const response = await this.apiClient.getAxiosInstance().put<ScheduledReportResponse>(
        `/api/reports/schedules/${scheduleId}`,
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a scheduled report
   *
   * @param scheduleId - Scheduled report identifier
   * @throws {ApiError} If the request fails
   */
  async deleteScheduledReport(scheduleId: string): Promise<void> {
    try {
      await this.apiClient.getAxiosInstance().delete(
        `/api/reports/schedules/${scheduleId}`
      );
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Error Handling ====================

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
 * Create a singleton instance of the Reports API client
 *
 * @param client - ApiClient instance
 * @returns ReportsClient instance
 */
export function createReportsClient(client: ApiClient): ReportsClient {
  return new ReportsClient(client);
}

export default ReportsClient;
