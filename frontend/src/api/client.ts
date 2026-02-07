/**
 * API Client for Resume Analysis Backend
 *
 * This module provides a typed Axios client for communicating with the
 * backend resume analysis service. Handles resume upload, analysis,
 * job matching, resume comparisons, and health check endpoints.
 *
 * Core functionality - domain-specific operations have been extracted to
 * separate modules in /frontend/src/api/.
 *
 * @example
 * ```ts
 * import { apiClient } from '@/api/client';
 *
 * // Upload resume
 * const uploadResult = await apiClient.uploadResume(file);
 *
 * // Analyze resume
 * const analysis = await apiClient.analyzeResume(uploadResult.id);
 *
 * // Compare with job vacancy
 * const match = await apiClient.compareWithVacancy(resumeId, vacancyData);
 *
 * // Compare multiple resumes
 * const comparison = await apiClient.compareMultipleResumes({
 *   vacancy_id: 'vacancy-123',
 *   resume_ids: ['resume1', 'resume2', 'resume3'],
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import {
  trackApiCall,
  logMetricsSummary,
  getPerformanceStats as getPerformanceStatsUtil,
  type PerformanceStats,
} from '@/utils/performanceTracker';
import { config } from '@/config';
import type {
  ResumeUploadResponse,
  AnalysisRequest,
  AnalysisResponse,
  JobVacancy,
  MatchResponse,
  HealthResponse,
  UploadProgressCallback,
  ApiClientConfig,
  ApiError,
  ComparisonCreate,
  ComparisonUpdate,
  ComparisonResponse,
  ComparisonListResponse,
  CompareMultipleRequest,
  ComparisonMatrixData,
} from '@/types/api';

/**
 * Default API configuration
 *
 * Uses centralized configuration service for all values.
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: config.api.url,
  timeout: config.api.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * API Client class
 *
 * Provides core methods for backend API endpoints with proper error handling,
 * type safety, and progress tracking for file uploads.
 *
 * Domain-specific operations have been extracted to separate modules:
 * - Skill taxonomies: @/api/skillTaxonomies
 * - Custom synonyms: @/api/customSynonyms
 * - Feedback: @/api/feedback
 * - Model versions: @/api/modelVersions
 * - Matching weights: @/api/matchingWeights
 * - ATS evaluation: @/api/atsEvaluation
 * - Analytics: @/api/analyticsClient
 * - Preferences: @/api/preferences
 * - Candidates: @/api/candidates
 * - Workflow stages: @/api/workflowStages
 * - Matching operations: @/api/matching
 */
export class ApiClient {
  private client: AxiosInstance;

  /**
   * Create a new API client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config: ApiClientConfig = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add timestamp for debugging
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
        // Calculate request duration
        const duration = Date.now() - (response.config.metadata?.startTime || 0);
        response.config.metadata = { ...response.config.metadata, duration };

        // Track performance metrics
        trackApiCall({
          endpoint: response.config.url || '',
          method: (response.config.method?.toUpperCase() || 'GET'),
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
        // Calculate request duration for failed requests
        const duration = Date.now() - (error.config?.metadata?.startTime || 0);

        // Track failed request metrics
        if (error.config) {
          trackApiCall({
            endpoint: error.config.url || '',
            method: (error.config.method?.toUpperCase() || 'GET'),
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

    // Default error messages by status code
    const defaultMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      413: 'File too large. Please upload a smaller file.',
      415: 'Unsupported file type. Please upload PDF or DOCX.',
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
   * Upload a resume file
   *
   * @param file - Resume file (PDF or DOCX)
   * @param onProgress - Optional progress callback (0-100)
   * @returns Upload response with resume ID
   * @throws ApiError if upload fails
   *
   * @example
   * ```ts
   * const result = await apiClient.uploadResume(file, (progress) => {
   *   console.log(`Upload progress: ${progress}%`);
   * });
   * ```
   */
  async uploadResume(
    file: File,
    onProgress?: UploadProgressCallback
  ): Promise<ResumeUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response: AxiosResponse<ResumeUploadResponse> = await this.client.post(
        '/api/resumes/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total && onProgress) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              onProgress(progress);
            }
          },
        }
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Analyze a resume
   *
   * @param request - Analysis request with resume ID and options
   * @returns Analysis results with keywords, entities, grammar, and experience
   * @throws ApiError if analysis fails
   *
   * @example
   * ```ts
   * const analysis = await apiClient.analyzeResume({
   *   resume_id: 'abc-123',
   *   extract_experience: true,
   *   check_grammar: true,
   * });
   * ```
   */
  async analyzeResume(request: AnalysisRequest): Promise<AnalysisResponse> {
    try {
      const response: AxiosResponse<AnalysisResponse> = await this.client.post(
        '/api/resumes/analyze',
        request
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Compare resume with job vacancy
   *
   * @param resumeId - Resume ID to compare
   * @param vacancy - Job vacancy data
   * @returns Match results with skill comparison and experience verification
   * @throws ApiError if comparison fails
   *
   * @example
   * ```ts
   * const match = await apiClient.compareWithVacancy('abc-123', {
   *   data: {
   *     position: 'Java Developer',
   *     mandatory_requirements: ['Java', 'Spring', 'SQL'],
   *   },
   * });
   * ```
   */
  async compareWithVacancy(resumeId: string, vacancy: JobVacancy): Promise<MatchResponse> {
    try {
      const response: AxiosResponse<MatchResponse> = await this.client.post(
        '/api/matching/compare',
        {
          resume_id: resumeId,
          vacancy_data: vacancy,
        }
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Check backend health status
   *
   * @returns Health status
   * @throws ApiError if health check fails
   */
  async healthCheck(): Promise<HealthResponse> {
    try {
      const response: AxiosResponse<HealthResponse> = await this.client.get('/health');
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Check if backend is ready
   *
   * @returns Ready status
   * @throws ApiError if check fails
   */
  async readyCheck(): Promise<{ status: string }> {
    try {
      const response: AxiosResponse<{ status: string }> = await this.client.get('/ready');
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
   * Useful for monitoring and debugging performance issues.
   *
   * @returns Performance statistics
   *
   * @example
   * ```ts
   * const stats = apiClient.getPerformanceStats();
   * console.log(`Average duration: ${stats.averageDuration}ms`);
   * console.log(`Total calls: ${stats.totalCalls}`);
   * ```
   */
  getPerformanceStats(): PerformanceStats {
    return getPerformanceStatsUtil();
  }

  /**
   * Log API performance summary to console
   *
   * Outputs a formatted summary of all API performance metrics to the console.
   * Useful for development and debugging.
   *
   * @example
   * ```ts
   * apiClient.logPerformanceSummary();
   * // Output:
   * // [API Performance Summary]
   * // Total calls: 45
   * // Average duration: 245ms
   * ```
   */
  logPerformanceSummary(): void {
    logMetricsSummary();
  }

  /**
   * Generic POST request for custom endpoints
   *
   * @param url - Endpoint URL
   * @param data - Request payload
   * @returns Response data
   * @throws ApiError if request fails
   */
  async post<T = unknown>(url: string, data?: unknown): Promise<AxiosResponse<T>> {
    try {
      return await this.client.post<T>(url, data);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Comparisons ====================

  /**
   * Create a new resume comparison view
   *
   * @param request - Create request with vacancy_id, resume_ids, and optional settings
   * @returns Created comparison view
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const result = await apiClient.createComparison({
   *   vacancy_id: 'vacancy-123',
   *   resume_ids: ['resume1', 'resume2', 'resume3'],
   *   name: 'Senior Developer Candidates',
   *   filters: { min_match_percentage: 50 },
   * });
   * ```
   */
  async createComparison(request: ComparisonCreate): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.post(
        '/api/comparisons/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List resume comparison views with optional filters and sorting
   *
   * @param vacancyId - Optional vacancy ID filter
   * @param createdBy - Optional creator user ID filter
   * @param minMatchPercentage - Optional minimum match percentage filter (0-100)
   * @param maxMatchPercentage - Optional maximum match percentage filter (0-100)
   * @param sortBy - Sort field - created_at, match_percentage, name, or updated_at
   * @param order - Sort order - asc or desc
   * @param limit - Maximum number of results to return (default: 50, max: 100)
   * @param offset - Number of results to skip (default: 0)
   * @returns List of comparison views
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const result = await apiClient.listComparisons(
   *   'vacancy-123',
   *   undefined,
   *   50,
   *   90,
   *   'match_percentage',
   *   'desc',
   *   10,
   *   0
   * );
   * ```
   */
  async listComparisons(
    vacancyId?: string,
    createdBy?: string,
    minMatchPercentage?: number,
    maxMatchPercentage?: number,
    sortBy?: string,
    order?: string,
    limit?: number,
    offset?: number
  ): Promise<ComparisonListResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (vacancyId) params.vacancy_id = vacancyId;
      if (createdBy) params.created_by = createdBy;
      if (minMatchPercentage !== undefined) params.min_match_percentage = minMatchPercentage;
      if (maxMatchPercentage !== undefined) params.max_match_percentage = maxMatchPercentage;
      if (sortBy) params.sort_by = sortBy;
      if (order) params.order = order;
      if (limit !== undefined) params.limit = limit;
      if (offset !== undefined) params.offset = offset;

      const response: AxiosResponse<ComparisonListResponse> = await this.client.get(
        '/api/comparisons/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific comparison view by ID
   *
   * @param id - Comparison view ID
   * @returns Comparison view details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const comparison = await apiClient.getComparison('comp-123');
   * ```
   */
  async getComparison(id: string): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.get(
        `/api/comparisons/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a comparison view
   *
   * @param id - Comparison view ID
   * @param request - Update request with fields to modify
   * @returns Updated comparison view
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await apiClient.updateComparison('comp-123', {
   *   name: 'Updated Comparison Name',
   *   filters: { min_match_percentage: 60 },
   * });
   * ```
   */
  async updateComparison(
    id: string,
    request: ComparisonUpdate
  ): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.put(
        `/api/comparisons/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a comparison view
   *
   * @param id - Comparison view ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await apiClient.deleteComparison('comp-123');
   * ```
   */
  async deleteComparison(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/comparisons/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Compare multiple resumes against a job vacancy
   *
   * This endpoint performs intelligent matching between each resume's skills
   * and the job vacancy requirements, handling synonyms (e.g., PostgreSQL ≈ SQL)
   * and providing aggregated results with ranking by match percentage.
   *
   * @param request - Compare request with vacancy_id and resume_ids
   * @returns Comparison matrix data with ranked results
   * @throws ApiError if comparison fails
   *
   * @example
   * ```ts
   * const result = await apiClient.compareMultipleResumes({
   *   vacancy_id: 'vacancy-123',
   *   resume_ids: ['resume1', 'resume2', 'resume3'],
   * });
   * // Returns ranked comparison results with match percentages
   * ```
   */
  async compareMultipleResumes(request: CompareMultipleRequest): Promise<ComparisonMatrixData> {
    try {
      const response: AxiosResponse<ComparisonMatrixData> = await this.client.post(
        '/api/comparisons/compare-multiple',
        request
      );
      return response.data;
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
 * Default API client instance
 *
 * Use this singleton instance for all API calls.
 */
export const apiClient = new ApiClient();

/**
 * Export API client class for custom instances
 */
export default ApiClient;
