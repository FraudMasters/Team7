/**
 * API Client for Resume Analysis Backend
 *
 * This module provides a typed Axios client for communicating with the
 * backend resume analysis service. Handles job matching, health check,
 * and other general API endpoints.
 *
 * For resume-specific operations (upload, analyze, list, delete), use the
 * ResumesClient from '@/api/resume' instead.
 *
 * @example
 * ```ts
 * import { apiClient } from '@/api/client';
 *
 * // Compare resume with job vacancy
 * const match = await apiClient.compareWithVacancy(resumeId, vacancyData);
 *
 * // Check backend health
 * const health = await apiClient.healthCheck();
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { config } from '@/config';
import type {
  JobVacancy,
  MatchResponse,
  HealthResponse,
  ApiClientConfig,
  ApiError,
  LanguagePreferenceResponse,
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

  /**
   * Update language preference
   *
   * @param language - Language code to set as preference
   * @returns Language preference response
   */
  async updateLanguagePreference(language: string): Promise<LanguagePreferenceResponse> {
    try {
      const response: AxiosResponse<LanguagePreferenceResponse> = await this.client.post(
        '/api/preferences/language',
        { language }
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
