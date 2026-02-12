/**
 * Filter Suggestions API Client
 *
 * This module provides a client for AI-powered job description
 * filter suggestions. It analyzes job descriptions and extracts
 * relevant search filters including skills, experience, location,
 * education, and languages with confidence scores.
 *
 * @example
 * ```ts
 * import { filterSuggestionsClient } from '@/api/filterSuggestions';
 *
 * // Get suggestions from raw JD text
 * const suggestions = await filterSuggestionsClient.suggestFilters({
 *   job_description: 'Senior Python Developer with 5+ years experience...',
 *   max_skills: 10,
 *   min_confidence: 0.5
 * });
 *
 * // Get suggestions from structured vacancy data
 * const suggestions = await filterSuggestionsClient.suggestFiltersFromVacancy({
 *   title: 'Senior Python Developer',
 *   skills: ['Python', 'Django', 'PostgreSQL'],
 *   requirements: ['Remote work available']
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { config } from '@/config';
import type { ApiError } from '@/types/api';

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Single suggested filter item with confidence scoring
 */
export interface SuggestedFilterItem {
  filter_type: string;
  value: string | string[] | number | boolean;
  confidence: number;
  source: 'extracted' | 'inferred' | 'synonym' | 'provided';
  original_text?: string;
}

/**
 * Request for JD filter suggestions
 */
export interface FilterSuggestionRequest {
  job_description: string;
  max_skills?: number;
  min_confidence?: number;
}

/**
 * Request for structured vacancy filter suggestions
 */
export interface VacancyFilterRequest {
  title?: string;
  description?: string;
  skills?: string[];
  requirements?: string[];
}

/**
 * Response from filter suggestions API
 */
export interface FilterSuggestionResponse {
  skills: SuggestedFilterItem[];
  min_experience_years: number | null;
  max_experience_years: number | null;
  seniority_level: string | null;
  location: SuggestedFilterItem | null;
  education_level: SuggestedFilterItem | null;
  languages: SuggestedFilterItem[];
  all_filters: SuggestedFilterItem[];
  confidence: number;
  analysis_time_seconds: number;
  search_filters: Record<string, unknown>;
}

/**
 * Alert settings update request
 */
export interface AlertSettingsUpdate {
  alert_enabled?: boolean;
  alert_frequency?: 'realtime' | 'daily' | 'weekly';
}

/**
 * Alert settings response
 */
export interface AlertSettingsResponse {
  id: string;
  name: string;
  alert_enabled: boolean;
  alert_frequency: string | null;
  last_alert_at: string | null;
}

/**
 * Apply saved search response (one-click apply)
 */
export interface ApplySearchResponse {
  saved_search_id: string;
  saved_search_name: string;
  total: number;
  candidates: Array<Record<string, unknown>>;
  query: string;
  filters_applied: Record<string, unknown>;
  execution_time_seconds: number;
}

// ============================================================================
// API Client
// ============================================================================

/**
 * Default API configuration for filter suggestions client
 */
const DEFAULT_CONFIG = {
  baseURL: config.api.url,
  timeout: 30000, // 30 seconds for AI processing
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Filter Suggestions API Client class
 *
 * Provides methods for AI-powered job description filter suggestions
 * with proper error handling and type safety.
 */
export class FilterSuggestionsClient {
  private client: AxiosInstance;

  /**
   * Create a new FilterSuggestions client instance
   *
   * @param clientConfig - Optional configuration overrides
   */
  constructor(clientConfig: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...clientConfig };

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
          detail: 'Request timeout. The analysis is taking too long. Please try again.',
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
      400: 'Invalid request. Please check your job description.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      422: 'Validation error. Please check your input.',
      429: 'Too many requests. Please try again later.',
      500: 'Server error during analysis. Please try again later.',
      502: 'Bad gateway. Please try again later.',
      503: 'Service unavailable. Please try again later.',
    };

    return {
      detail: data?.detail || defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * Analyze a job description and suggest search filters
   *
   * Uses AI-powered analysis to extract relevant search filters
   * from job description text. Identifies skills, experience requirements,
   * location preferences, education requirements, and language requirements.
   *
   * @param request - Request containing job description and options
   * @returns Suggested filters with confidence scores
   * @throws ApiError if analysis fails
   *
   * @example
   * ```ts
   * const suggestions = await filterSuggestionsClient.suggestFilters({
   *   job_description: 'Senior Python Developer with 5+ years experience in Django and AWS...',
   *   max_skills: 10,
   *   min_confidence: 0.5
   * });
   *
   * console.log(suggestions.skills);
   * // [{ filter_type: 'skills', value: 'Python', confidence: 0.95, ... }]
   *
   * console.log(suggestions.min_experience_years);
   * // 5
   *
   * // Use ready-to-apply filters
   * const searchResults = await candidateSearchClient.searchCandidates({
   *   filters: suggestions.search_filters
   * });
   * ```
   */
  async suggestFilters(request: FilterSuggestionRequest): Promise<FilterSuggestionResponse> {
    try {
      const response: AxiosResponse<FilterSuggestionResponse> = await this.client.post(
        '/api/filter-suggestions/suggest',
        {
          job_description: request.job_description,
          max_skills: request.max_skills ?? 10,
          min_confidence: request.min_confidence ?? 0.5,
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Analyze structured vacancy data and suggest search filters
   *
   * Accepts structured vacancy data (title, description, skills list,
   * requirements) and generates filter suggestions. Use this when you
   * have already-parsed vacancy data rather than raw text.
   *
   * @param request - Structured vacancy data
   * @returns Suggested filters with confidence scores
   * @throws ApiError if analysis fails
   *
   * @example
   * ```ts
   * const suggestions = await filterSuggestionsClient.suggestFiltersFromVacancy({
   *   title: 'Senior Python Developer',
   *   description: '5+ years experience required',
   *   skills: ['Python', 'Django', 'PostgreSQL'],
   *   requirements: ['Remote work available', 'BS in CS preferred']
   * });
   *
   * console.log(suggestions.skills);
   * // Skills extracted from both the skills array and description
   * ```
   */
  async suggestFiltersFromVacancy(request: VacancyFilterRequest): Promise<FilterSuggestionResponse> {
    try {
      const response: AxiosResponse<FilterSuggestionResponse> = await this.client.post(
        '/api/filter-suggestions/suggest-vacancy',
        {
          title: request.title ?? null,
          description: request.description ?? null,
          skills: request.skills ?? null,
          requirements: request.requirements ?? null,
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Apply a saved search with one-click execution
   *
   * Executes a saved search and returns the matching candidates.
   * This is a convenience method that wraps the saved search apply endpoint.
   *
   * @param savedSearchId - UUID of the saved search to apply
   * @returns Search results with matching candidates
   * @throws ApiError if application fails
   *
   * @example
   * ```ts
   * const results = await filterSuggestionsClient.applySavedSearch('search-uuid');
   * console.log(`Found ${results.total} matching candidates`);
   * ```
   */
  async applySavedSearch(savedSearchId: string): Promise<ApplySearchResponse> {
    try {
      const response: AxiosResponse<ApplySearchResponse> = await this.client.post(
        `/api/saved-searches/${savedSearchId}/apply`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update alert settings for a saved search
   *
   * @param savedSearchId - UUID of the saved search
   * @param settings - Alert settings to update
   * @returns Updated alert settings
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const settings = await filterSuggestionsClient.updateAlertSettings('search-uuid', {
   *   alert_enabled: true,
   *   alert_frequency: 'daily'
   * });
   * ```
   */
  async updateAlertSettings(
    savedSearchId: string,
    settings: AlertSettingsUpdate
  ): Promise<AlertSettingsResponse> {
    try {
      const response: AxiosResponse<AlertSettingsResponse> = await this.client.put(
        `/api/saved-searches/${savedSearchId}/alert-settings`,
        settings
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get alert settings for a saved search
   *
   * @param savedSearchId - UUID of the saved search
   * @returns Current alert settings
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const settings = await filterSuggestionsClient.getAlertSettings('search-uuid');
   * console.log(`Alerts enabled: ${settings.alert_enabled}`);
   * ```
   */
  async getAlertSettings(savedSearchId: string): Promise<AlertSettingsResponse> {
    try {
      const response: AxiosResponse<AlertSettingsResponse> = await this.client.get(
        `/api/saved-searches/${savedSearchId}/alert-settings`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

// ============================================================================
// Singleton Export
// ============================================================================

/**
 * Default filter suggestions client instance
 *
 * Pre-configured with the application's API base URL and standard
 * timeout settings. Use this for most filter suggestion operations.
 *
 * @example
 * ```ts
 * import { filterSuggestionsClient } from '@/api/filterSuggestions';
 *
 * const suggestions = await filterSuggestionsClient.suggestFilters({
 *   job_description: 'Senior Python Developer...'
 * });
 * ```
 */
export const filterSuggestionsClient = new FilterSuggestionsClient();

/**
 * Create a custom filter suggestions client
 *
 * Factory function for creating a filter suggestions client with
 * custom configuration (e.g., different base URL, longer timeout).
 *
 * @param clientConfig - Custom configuration options
 * @returns Configured filter suggestions client
 *
 * @example
 * ```ts
 * import { createFilterSuggestionsClient } from '@/api/filterSuggestions';
 *
 * const customClient = createFilterSuggestionsClient({
 *   timeout: 60000 // Longer timeout for large JDs
 * });
 * ```
 */
export function createFilterSuggestionsClient(
  clientConfig: Partial<typeof DEFAULT_CONFIG>
): FilterSuggestionsClient {
  return new FilterSuggestionsClient(clientConfig);
}
