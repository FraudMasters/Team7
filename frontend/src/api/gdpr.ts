/**
 * GDPR API Client
 *
 * This module provides a typed client for communicating with the
 * backend GDPR compliance service. Handles consent management,
 * data deletion requests (right to be forgotten), data export
 * (right to portability), retention policies, cookie consent,
 * and processing agreements.
 *
 * @example
 * ```ts
 * import { gdprClient } from '@/api/gdpr';
 *
 * // Grant consent
 * const consent = await gdprClient.grantConsent({
 *   consent_type: 'data_processing',
 *   granted: true,
 * });
 *
 * // Request data deletion
 * const deletion = await gdprClient.createDataDeletionRequest({
 *   resume_id: 'resume-123',
 *   reason: 'Right to be forgotten',
 * });
 *
 * // Export personal data
 * const exportData = await gdprClient.exportPersonalData('resume-123');
 *
 * // Create retention policy
 * const policy = await gdprClient.createRetentionPolicy({
 *   policy_name: 'Default Retention',
 *   entity_type: 'resume',
 *   retention_days: 365,
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
  ApiError,
  ApiClientConfig,
  ConsentRecordRequest,
  ConsentRecordResponse,
  ConsentListResponse,
  ConsentStatusResponse,
  WithdrawConsentRequest,
  DataDeletionRequest,
  DataDeletionRequestResponse,
  DataDeletionRequestListItem,
  PersonalDataExport,
  OrganizationDataExportResponse,
  RetentionPolicyCreate,
  RetentionPolicyUpdate,
  RetentionPolicyResponse,
  RetentionPolicyListResponse,
  CookieConsentResponse,
  CookieConsentUpdate,
  ProcessingAgreementCreate,
  ProcessingAgreementUpdate,
  ProcessingAgreementResponse,
  ProcessingAgreementListResponse,
} from '@/types/api';

/**
 * Default API configuration for GDPR endpoints
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * GDPR API Client class
 *
 * Provides methods for all GDPR-related API endpoints with proper error handling,
 * type safety, and performance tracking.
 */
export class GDPRClient {
  private client: AxiosInstance;

  /**
   * Create a new GDPR API client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config: ApiClientConfig = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        config.metadata = { startTime: Date.now() };
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
          responseSize: response.headers['content-length']
            ? parseInt(response.headers['content-length'], 10)
            : undefined,
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
    const axiosError = error as AxiosError<{ detail?: string }>;

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

    const status = axiosError.response.status;
    const data = axiosError.response.data;

    if (data?.detail) {
      return { detail: data.detail, status };
    }

    const defaultMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      422: 'Validation error. Please check your input.',
      429: 'Too many requests. Please try again later.',
      500: 'Server error. Please try again later.',
      502: 'Bad gateway. Please try again later.',
      503: 'Service unavailable. Please try again later.',
    };

    return {
      detail: data?.detail || defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * Get the underlying Axios instance
   *
   * @returns Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }

  /**
   * Get API performance statistics
   *
   * @returns Performance statistics
   */
  getPerformanceStats(): PerformanceStats {
    return getPerformanceStatsUtil();
  }

  // ==================== Consent Management ====================

  /**
   * Grant or update consent
   *
   * @param request - Consent record request
   * @returns Consent record response
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const consent = await gdprClient.grantConsent({
   *   consent_type: 'data_processing',
   *   granted: true,
   *   user_id: 'user-123',
   * });
   * ```
   */
  async grantConsent(request: ConsentRecordRequest): Promise<ConsentRecordResponse> {
    try {
      const response: AxiosResponse<ConsentRecordResponse> = await this.client.post(
        '/api/consent/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List consent records with optional filters
   *
   * @param userId - Optional user ID filter
   * @param organizationId - Optional organization ID filter
   * @param consentType - Optional consent type filter
   * @param isActive - Optional active status filter
   * @returns List of consent records
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const consents = await gdprClient.listConsents('user-123', undefined, 'data_processing');
   * ```
   */
  async listConsents(
    userId?: string,
    organizationId?: string,
    consentType?: string,
    isActive?: boolean
  ): Promise<ConsentListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (userId) params.user_id = userId;
      if (organizationId) params.organization_id = organizationId;
      if (consentType) params.consent_type = consentType;
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<ConsentListResponse> = await this.client.get(
        '/api/consent/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific consent record by ID
   *
   * @param consentId - Consent record ID
   * @returns Consent record details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const consent = await gdprClient.getConsent('consent-123');
   * ```
   */
  async getConsent(consentId: string): Promise<ConsentRecordResponse> {
    try {
      const response: AxiosResponse<ConsentRecordResponse> = await this.client.get(
        `/api/consent/${consentId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Check consent status for a user/organization
   *
   * @param consentType - Consent type to check
   * @param userId - Optional user ID
   * @param organizationId - Optional organization ID
   * @returns Consent status
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const status = await gdprClient.checkConsentStatus('data_processing', 'user-123');
   * if (status.has_consent) {
   *   console.log('User has granted consent');
   * }
   * ```
   */
  async checkConsentStatus(
    consentType: string,
    userId?: string,
    organizationId?: string
  ): Promise<ConsentStatusResponse> {
    try {
      const params: Record<string, string> = { consent_type: consentType };
      if (userId) params.user_id = userId;
      if (organizationId) params.organization_id = organizationId;

      const response: AxiosResponse<ConsentStatusResponse> = await this.client.get(
        '/api/consent/check',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Withdraw consent
   *
   * @param request - Withdraw consent request
   * @returns Updated consent record
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const consent = await gdprClient.withdrawConsent({
   *   consent_type: 'data_processing',
   *   user_id: 'user-123',
   *   reason: 'No longer wish to share data',
   * });
   * ```
   */
  async withdrawConsent(request: WithdrawConsentRequest): Promise<ConsentRecordResponse> {
    try {
      const response: AxiosResponse<ConsentRecordResponse> = await this.client.post(
        '/api/consent/withdraw',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Data Deletion (Right to be Forgotten) ====================

  /**
   * Create a data deletion request
   *
   * @param request - Data deletion request
   * @returns Deletion request response
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const deletion = await gdprClient.createDataDeletionRequest({
   *   resume_id: 'resume-123',
   *   reason: 'Right to be forgotten',
   *   requester_email: 'user@example.com',
   * });
   * ```
   */
  async createDataDeletionRequest(
    request: DataDeletionRequest
  ): Promise<DataDeletionRequestResponse> {
    try {
      const response: AxiosResponse<DataDeletionRequestResponse> = await this.client.post(
        '/api/data-deletion/request',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List data deletion requests
   *
   * @param status - Optional status filter (pending, processing, completed, cancelled)
   * @param limit - Maximum number of results (default: 50)
   * @param offset - Number of results to skip (default: 0)
   * @returns List of data deletion requests
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const requests = await gdprClient.listDataDeletionRequests('pending', 20, 0);
   * ```
   */
  async listDataDeletionRequests(
    status?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<DataDeletionRequestListItem[]> {
    try {
      const params: Record<string, number | string> = { limit, offset };
      if (status) params.status = status;

      const response: AxiosResponse<DataDeletionRequestListItem[]> = await this.client.get(
        '/api/data-deletion/requests',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific data deletion request by ID
   *
   * @param requestId - Deletion request ID
   * @returns Deletion request details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const request = await gdprClient.getDataDeletionRequest('request-123');
   * ```
   */
  async getDataDeletionRequest(requestId: string): Promise<DataDeletionRequestListItem> {
    try {
      const response: AxiosResponse<DataDeletionRequestListItem> = await this.client.get(
        `/api/data-deletion/requests/${requestId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Process a pending deletion request
   *
   * @param requestId - Deletion request ID
   * @returns Success message
   * @throws ApiError if processing fails
   *
   * @example
   * ```ts
   * await gdprClient.processDataDeletion('request-123');
   * ```
   */
  async processDataDeletion(requestId: string): Promise<{ message: string }> {
    try {
      const response: AxiosResponse<{ message: string }> = await this.client.post(
        `/api/data-deletion/requests/${requestId}/process`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Cancel a pending deletion request
   *
   * @param requestId - Deletion request ID
   * @returns Success message
   * @throws ApiError if cancellation fails
   *
   * @example
   * ```ts
   * await gdprClient.cancelDataDeletion('request-123');
   * ```
   */
  async cancelDataDeletion(requestId: string): Promise<{ message: string }> {
    try {
      const response: AxiosResponse<{ message: string }> = await this.client.post(
        `/api/data-deletion/requests/${requestId}/cancel`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Data Export (Right to Portability) ====================

  /**
   * Export personal data for a specific resume
   *
   * @param resumeId - Resume ID
   * @param format - Export format ('json' or 'csv', default: 'json')
   * @returns Personal data export
   * @throws ApiError if export fails
   *
   * @example
   * ```ts
   * const exportData = await gdprClient.exportPersonalData('resume-123', 'json');
   * console.log(exportData.hiring_stages);
   * console.log(exportData.notes);
   * ```
   */
  async exportPersonalData(
    resumeId: string,
    format: string = 'json'
  ): Promise<PersonalDataExport> {
    try {
      const response: AxiosResponse<PersonalDataExport> = await this.client.get(
        `/api/data-export/resume/${resumeId}`,
        { params: { format } }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Export all data for an organization
   *
   * @param organizationId - Organization ID
   * @param format - Export format ('json' or 'csv', default: 'json')
   * @returns Organization data export
   * @throws ApiError if export fails
   *
   * @example
   * ```ts
   * const orgData = await gdprClient.exportOrganizationData('org-123', 'csv');
   * console.log(`${orgData.total_records} records exported`);
   * ```
   */
  async exportOrganizationData(
    organizationId: string,
    format: string = 'json'
  ): Promise<OrganizationDataExportResponse> {
    try {
      const response: AxiosResponse<OrganizationDataExportResponse> = await this.client.get(
        `/api/data-export/organization/${organizationId}`,
        { params: { format } }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Retention Policies ====================

  /**
   * Create a data retention policy
   *
   * @param request - Retention policy create request
   * @returns Created retention policy
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const policy = await gdprClient.createRetentionPolicy({
   *   policy_name: 'Default Resume Retention',
   *   entity_type: 'resume',
   *   retention_days: 365,
   *   action_type: 'delete',
   *   is_active: true,
   * });
   * ```
   */
  async createRetentionPolicy(
    request: RetentionPolicyCreate
  ): Promise<RetentionPolicyResponse> {
    try {
      const response: AxiosResponse<RetentionPolicyResponse> = await this.client.post(
        '/api/retention-policies/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List retention policies
   *
   * @param organizationId - Optional organization ID filter
   * @param entityType - Optional entity type filter
   * @param isActive - Optional active status filter
   * @returns List of retention policies
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const policies = await gdprClient.listRetentionPolicies('org-123', 'resume', true);
   * ```
   */
  async listRetentionPolicies(
    organizationId?: string,
    entityType?: string,
    isActive?: boolean
  ): Promise<RetentionPolicyListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (entityType) params.entity_type = entityType;
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<RetentionPolicyListResponse> = await this.client.get(
        '/api/retention-policies/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific retention policy by ID
   *
   * @param policyId - Retention policy ID
   * @returns Retention policy details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const policy = await gdprClient.getRetentionPolicy('policy-123');
   * ```
   */
  async getRetentionPolicy(policyId: string): Promise<RetentionPolicyResponse> {
    try {
      const response: AxiosResponse<RetentionPolicyResponse> = await this.client.get(
        `/api/retention-policies/${policyId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a retention policy
   *
   * @param policyId - Retention policy ID
   * @param request - Update request
   * @returns Updated retention policy
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await gdprClient.updateRetentionPolicy('policy-123', {
   *   retention_days: 730,
   *   is_active: false,
   * });
   * ```
   */
  async updateRetentionPolicy(
    policyId: string,
    request: RetentionPolicyUpdate
  ): Promise<RetentionPolicyResponse> {
    try {
      const response: AxiosResponse<RetentionPolicyResponse> = await this.client.put(
        `/api/retention-policies/${policyId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a retention policy
   *
   * @param policyId - Retention policy ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await gdprClient.deleteRetentionPolicy('policy-123');
   * ```
   */
  async deleteRetentionPolicy(policyId: string): Promise<void> {
    try {
      await this.client.delete(`/api/retention-policies/${policyId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Cookie Consent ====================

  /**
   * Get current cookie consent preferences
   *
   * @returns Cookie consent response
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const consent = await gdprClient.getCookieConsent();
   * console.log('Analytics:', consent.analytics);
   * console.log('Marketing:', consent.marketing);
   * ```
   */
  async getCookieConsent(): Promise<CookieConsentResponse> {
    try {
      const response: AxiosResponse<CookieConsentResponse> = await this.client.get(
        '/api/cookie-consent/'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update cookie consent preferences
   *
   * @param request - Cookie consent update request
   * @returns Updated cookie consent response
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const consent = await gdprClient.updateCookieConsent({
   *   analytics: true,
   *   marketing: false,
   * });
   * ```
   */
  async updateCookieConsent(request: CookieConsentUpdate): Promise<CookieConsentResponse> {
    try {
      const response: AxiosResponse<CookieConsentResponse> = await this.client.post(
        '/api/cookie-consent/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Processing Agreements (DPA) ====================

  /**
   * Create a processing agreement (DPA)
   *
   * @param request - Processing agreement create request
   * @returns Created processing agreement
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const agreement = await gdprClient.createProcessingAgreement({
   *   organization_id: 'org-123',
   *   vendor_name: 'Cloud Storage Provider',
   *   vendor_contact_email: 'dpa@vendor.com',
   *   purpose_description: 'Data backup and storage',
   *   data_categories: ['resumes', 'candidate_data'],
   *   processing_activities: ['storage', 'backup'],
   *   retention_period: '365 days',
   *   security_measures: 'Encryption at rest and in transit',
   *   data_location: 'EU',
   * });
   * ```
   */
  async createProcessingAgreement(
    request: ProcessingAgreementCreate
  ): Promise<ProcessingAgreementResponse> {
    try {
      const response: AxiosResponse<ProcessingAgreementResponse> = await this.client.post(
        '/api/processing-agreements/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List processing agreements
   *
   * @param organizationId - Optional organization ID filter
   * @param status - Optional status filter (active, expired, revoked)
   * @returns List of processing agreements
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const agreements = await gdprClient.listProcessingAgreements('org-123', 'active');
   * ```
   */
  async listProcessingAgreements(
    organizationId?: string,
    status?: string
  ): Promise<ProcessingAgreementListResponse> {
    try {
      const params: Record<string, string> = {};
      if (organizationId) params.organization_id = organizationId;
      if (status) params.status = status;

      const response: AxiosResponse<ProcessingAgreementListResponse> = await this.client.get(
        '/api/processing-agreements/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific processing agreement by ID
   *
   * @param agreementId - Processing agreement ID
   * @returns Processing agreement details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const agreement = await gdprClient.getProcessingAgreement('agreement-123');
   * ```
   */
  async getProcessingAgreement(agreementId: string): Promise<ProcessingAgreementResponse> {
    try {
      const response: AxiosResponse<ProcessingAgreementResponse> = await this.client.get(
        `/api/processing-agreements/${agreementId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a processing agreement
   *
   * @param agreementId - Processing agreement ID
   * @param request - Update request
   * @returns Updated processing agreement
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await gdprClient.updateProcessingAgreement('agreement-123', {
   *   status: 'active',
   *   review_date: '2025-12-31',
   * });
   * ```
   */
  async updateProcessingAgreement(
    agreementId: string,
    request: ProcessingAgreementUpdate
  ): Promise<ProcessingAgreementResponse> {
    try {
      const response: AxiosResponse<ProcessingAgreementResponse> = await this.client.put(
        `/api/processing-agreements/${agreementId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a processing agreement
   *
   * @param agreementId - Processing agreement ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await gdprClient.deleteProcessingAgreement('agreement-123');
   * ```
   */
  async deleteProcessingAgreement(agreementId: string): Promise<void> {
    try {
      await this.client.delete(`/api/processing-agreements/${agreementId}`);
    } catch (error) {
      throw this.transformError(error);
    }
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
 * Default GDPR API client instance
 *
 * Use this singleton instance for all GDPR API calls.
 */
export const gdprClient = new GDPRClient();

/**
 * Export GDPR client class for custom instances
 */
export default GDPRClient;
