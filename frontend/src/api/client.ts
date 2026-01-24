/**
 * API Client for Resume Analysis Backend
 *
 * This module provides a typed Axios client for communicating with the
 * backend resume analysis service. Handles resume upload, analysis,
 * job matching, and health check endpoints.
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
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
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
} from '@/types/api';

/**
 * Default API configuration
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 120000, // 2 minutes for long-running analysis
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * API Client class
 *
 * Provides methods for all backend API endpoints with proper error handling,
 * type safety, and progress tracking for file uploads.
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
        return response;
      },
      (error) => {
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
