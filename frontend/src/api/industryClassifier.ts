/**
 * Industry Classifier API Client
 *
 * This module provides a typed client for communicating with the
 * industry classification backend service. Handles industry detection
 * from job titles and descriptions, as well as skill suggestions
 * based on industry context.
 *
 * @example
 * ```ts
 * import { industryClassifier } from '@/api/industryClassifier';
 *
 * // Classify industry from job title
 * const classification = await industryClassifier.classifyIndustry({
 *   title: 'Senior Registered Nurse',
 *   description: 'Looking for an experienced RN with ICU experience...',
 * });
 *
 * // Get skill suggestions for a specific industry
 * const suggestions = await industryClassifier.getSuggestions({
 *   industry: 'healthcare',
 *   title: 'Senior Registered Nurse',
 *   description: 'ICU, patient care, medical records...',
 *   limit: 20,
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  IndustryClassificationRequest,
  IndustryClassificationResponse,
  SkillSuggestionRequest,
  SkillSuggestionResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for industry classifier
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 30000, // 30 seconds for classification
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Industry Classifier API Client class
 *
 * Provides methods for industry classification and skill suggestions
 * with proper error handling and type safety.
 */
export class IndustryClassifierClient {
  private client: AxiosInstance;

  /**
   * Create a new Industry Classifier client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = {
      ...DEFAULT_CONFIG,
      ...config,
      headers: {
        ...DEFAULT_CONFIG.headers,
        ...config.headers,
      },
    };

    this.client = axios.create(finalConfig);

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(this.transformError(error))
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
   * Classify industry from job title and optional description
   *
   * @param request - Classification request with title and optional description
   * @returns Industry classification with confidence score
   * @throws ApiError if classification fails
   *
   * @example
   * ```ts
   * const result = await industryClassifier.classifyIndustry({
   *   title: 'Senior Java Developer',
   *   description: 'Looking for a backend developer with Spring experience...',
   * });
   * // Returns: { industry: 'tech', confidence: 0.95, ... }
   * ```
   */
  async classifyIndustry(
    request: IndustryClassificationRequest
  ): Promise<IndustryClassificationResponse> {
    try {
      const response: AxiosResponse<IndustryClassificationResponse> = await this.client.post(
        '/api/industry-classifier/classify',
        request
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get skill suggestions based on industry and job context
   *
   * @param request - Suggestion request with industry, title, description, and limit
   * @returns Skill suggestions with relevance scores
   * @throws ApiError if suggestion fails
   *
   * @example
   * ```ts
   * const suggestions = await industryClassifier.getSuggestions({
   *   industry: 'healthcare',
   *   title: 'Senior Registered Nurse',
   *   description: 'ICU, patient care, medical records...',
   *   limit: 20,
   * });
   * // Returns: { industry: 'healthcare', suggested_skills: [...], total_count: 15 }
   * ```
   */
  async getSuggestions(
    request: SkillSuggestionRequest
  ): Promise<SkillSuggestionResponse> {
    try {
      const response: AxiosResponse<SkillSuggestionResponse> = await this.client.post(
        '/api/skill-suggestions/suggest',
        request
      );

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

/**
 * Default industry classifier client instance
 *
 * Use this singleton instance for all industry classification calls.
 */
export const industryClassifier = new IndustryClassifierClient();

/**
 * Export industry classifier client class for custom instances
 */
export default IndustryClassifierClient;
