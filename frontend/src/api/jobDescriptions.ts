/**
 * Job Descriptions API Client
 *
 * This module provides a client for generating AI-powered job descriptions.
 * It uses LLMs to create professional, inclusive, and compelling job
 * descriptions based on role title, required skills, and experience requirements.
 *
 * @example
 * ```ts
 * import { jobDescriptionsClient, JobDescriptionsClient } from '@/api/jobDescriptions';
 *
 * // Generate a job description
 * const description = await jobDescriptionsClient.generateDescription({
 *   title: 'Senior Python Developer',
 *   required_skills: ['Python', 'Django', 'PostgreSQL'],
 *   min_experience_months: 60,
 *   seniority_level: 'senior',
 *   industry: 'Technology',
 *   work_format: 'remote',
 *   tone: 'professional',
 *   language: 'en'
 * });
 *
 * console.log(description.summary);
 * console.log(description.responsibilities);
 * console.log(description.requirements);
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ApiError,
  JobDescriptionGenerateRequest,
  JobDescriptionResponse,
} from '@/types/api';

/**
 * Re-export types for convenience
 */
export type {
  JobDescriptionGenerateRequest,
  JobDescriptionResponse,
};

/**
 * Default configuration for the job descriptions client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 60000, // 60 seconds (LLM generation can take longer)
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Job Descriptions API Client class
 *
 * Provides methods for generating AI-powered job descriptions with proper
 * error handling and type safety.
 */
export class JobDescriptionsClient {
  private client: AxiosInstance;

  /**
   * Create a new JobDescriptions client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

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
   * Generate a professional job description based on role requirements
   *
   * This endpoint creates comprehensive, inclusive job descriptions using LLMs.
   * The description includes a summary, key responsibilities, requirements,
   * benefits, company culture overview, and interview process information.
   *
   * @param request - Generate request with job details
   * @returns Generated job description with all sections
   * @throws ApiError if generation fails
   *
   * @example
   * ```ts
   * const description = await jobDescriptionsClient.generateDescription({
   *   title: 'Senior Python Developer',
   *   required_skills: ['Python', 'Django', 'PostgreSQL'],
   *   min_experience_months: 60,
   *   seniority_level: 'senior',
   *   industry: 'Technology',
   *   work_format: 'remote',
   *   location: 'Remote',
   *   employment_type: 'full-time',
   *   salary_range: '$80,000 - $120,000',
   *   additional_requirements: ['Docker', 'Kubernetes', 'Redis'],
   *   tone: 'professional',
   *   language: 'en'
   * });
   *
   * console.log(description.summary);
   * console.log(description.responsibilities);
   * console.log(description.requirements);
   * console.log(description.benefits);
   * ```
   */
  async generateDescription(request: JobDescriptionGenerateRequest): Promise<JobDescriptionResponse> {
    try {
      const response: AxiosResponse<JobDescriptionResponse> = await this.client.post(
        '/api/job-descriptions/generate',
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
 * Default job descriptions client instance
 *
 * Use this singleton instance for all job description API calls.
 */
export const jobDescriptionsClient = new JobDescriptionsClient();

/**
 * Export job descriptions client class for custom instances
 */
export default JobDescriptionsClient;
