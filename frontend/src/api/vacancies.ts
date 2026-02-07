/**
 * Vacancy API Client
 *
 * This module provides clients for working with vacancies:
 * - VacanciesClient: CRUD operations for vacancy management
 * - VacancySearchClient: Advanced search with filtering
 *
 * @example
 * ```ts
 * import { vacanciesClient, vacancySearchClient } from '@/api/vacancies';
 *
 * // CRUD operations
 * const vacancies = await vacanciesClient.listVacancies();
 * const vacancy = await vacanciesClient.getVacancy('vacancy-123');
 *
 * // Search operations
 * const results = await vacancySearchClient.searchVacancies({
 *   query: 'software engineer',
 *   filters: { work_format: 'remote' }
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  JobVacancy,
  ApiError,
  VacancyCreate,
  VacancyUpdate,
  VacancyResponse,
  VacancyListResponse,
  VacancyBulkImportRequest,
  VacancyBulkImportResponse,
  VacancySearchRequest,
  VacancySearchResponse,
} from '@/types/api';

/**
 * Re-export types for convenience
 */
export type {
  VacancyCreate,
  VacancyUpdate,
  VacancyResponse,
  VacancyListResponse,
  VacancyBulkImportRequest,
  VacancyBulkImportResponse,
  VacancySearchRequest,
  VacancySearchResponse,
};

/**
 * Default API configuration
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Base class with common functionality
 */
abstract class BaseVacancyClient {
  protected client: AxiosInstance;

  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };
    this.client = axios.create(finalConfig);

    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(this.transformError(error))
    );
  }

  protected transformError(error: unknown): ApiError {
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

  getAxiosInstance(): AxiosInstance {
    return this.client;
  }
}

/**
 * CRUD API Client for Vacancies
 *
 * Provides methods for creating, reading, updating, and deleting vacancies.
 */
export class VacanciesClient extends BaseVacancyClient {
  /**
   * Get all vacancies with pagination and optional filters
   */
  async listVacancies(
    skip: number = 0,
    limit: number = 100,
    industry?: string,
    position?: string
  ): Promise<VacancyListResponse> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (industry) params.industry = industry;
      if (position) params.position = position;

      const response: AxiosResponse<VacancyListResponse> = await this.client.get(
        '/api/vacancies',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a vacancy by ID
   */
  async getVacancy(id: string): Promise<VacancyResponse> {
    try {
      const response: AxiosResponse<VacancyResponse> = await this.client.get(
        `/api/vacancies/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Create a new vacancy
   */
  async createVacancy(data: VacancyCreate): Promise<VacancyResponse> {
    try {
      const response: AxiosResponse<VacancyResponse> = await this.client.post(
        '/api/vacancies',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update an existing vacancy
   */
  async updateVacancy(id: string, data: VacancyUpdate): Promise<VacancyResponse> {
    try {
      const response: AxiosResponse<VacancyResponse> = await this.client.put(
        `/api/vacancies/${id}`,
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a vacancy
   */
  async deleteVacancy(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/vacancies/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Bulk import vacancies
   */
  async bulkImport(request: VacancyBulkImportRequest): Promise<VacancyBulkImportResponse> {
    try {
      const response: AxiosResponse<VacancyBulkImportResponse> = await this.client.post(
        '/api/vacancies/bulk',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

/**
 * Search API Client for Vacancies
 *
 * Provides advanced search functionality with filters and boolean operators.
 */
export class VacancySearchClient extends BaseVacancyClient {
  /**
   * Search for vacancies with advanced filters
   *
   * @example
   * ```ts
   * const results = await vacancySearchClient.searchVacancies({
   *   query: 'software engineer',
   *   filters: {
   *     work_format: 'remote',
   *     employment_type: 'full-time',
   *     salary_min: 80000,
   *     salary_max: 120000
   *   },
   *   limit: 10,
   *   sort_by: 'date'
   * });
   * ```
   */
  async searchVacancies(request: VacancySearchRequest = {}): Promise<VacancySearchResponse> {
    try {
      const response: AxiosResponse<VacancySearchResponse> = await this.client.post(
        '/api/vacancies/search',
        {
          query: request.query ?? null,
          filters: request.filters ?? null,
          skip: request.skip ?? 0,
          limit: request.limit ?? 100,
          sort_by: request.sort_by ?? 'date',
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

/**
 * Default client instances
 */
export const vacanciesClient = new VacanciesClient();
export const vacancySearchClient = new VacancySearchClient();

/**
 * Export clients for creating custom instances
 */
export { VacanciesClient as default, VacancySearchClient };
