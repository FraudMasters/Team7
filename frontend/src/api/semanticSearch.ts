/**
 * Semantic Search API Client
 *
 * This module provides a client for LLM-powered semantic search with
 * natural language queries, hybrid search combining semantic and keyword
 * matching, and detailed match explanations.
 *
 * @example
 * ```ts
 * import { semanticSearchClient } from '@/api/semanticSearch';
 *
 * // Natural language semantic search
 * const results = await semanticSearchClient.semanticSearch({
 *   query: 'Find senior Python developers with team leadership experience',
 *   limit: 10
 * });
 *
 * // Hybrid search with configurable weights
 * const results = await semanticSearchClient.hybridSearch({
 *   query: 'React developer with TypeScript',
 *   semantic_weight: 0.6,
 *   keyword_weight: 0.4,
 *   filters: {
 *     min_experience_years: 3
 *   }
 * });
 *
 * // Get match explanation for a specific candidate
 * const explanation = await semanticSearchClient.explainMatch({
 *   query: 'Senior Python developer with fintech experience',
 *   resume_id: 'resume-uuid'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  SemanticSearchRequest,
  SemanticSearchResponse,
  HybridSearchRequest,
  HybridSearchResponse,
  MatchExplanationRequest,
  MatchExplanationResponse,
  SemanticSearchFilters,
  SemanticMatchExplanation,
  SemanticCandidateResult,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration for semantic search client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 30000, // 30 seconds (LLM queries can take longer)
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Semantic Search API Client class
 *
 * Provides methods for LLM-powered semantic search with proper
 * error handling and type safety.
 */
export class SemanticSearchClient {
  private client: AxiosInstance;

  /**
   * Create a new SemanticSearch client instance
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
          detail: 'Request timeout. Semantic search may take longer - please try again.',
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
      400: 'Invalid search parameters. Please check your query.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      422: 'Validation error. Please check your search criteria.',
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
   * Semantic search for candidates using natural language queries
   *
   * Supports natural language queries like "Find senior Python developers with
   * team leadership experience" using LLM-powered semantic understanding.
   *
   * @param request - Search request with query, filters, and scoring options
   * @returns Search results with candidate list and semantic scores
   * @throws ApiError if search fails
   *
   * @example
   * ```ts
   * // Natural language search
   * const results = await semanticSearchClient.semanticSearch({
   *   query: 'Find senior Python developers with team leadership experience',
   *   limit: 10
   * });
   *
   * // Search with vacancy context
   * const results = await semanticSearchClient.semanticSearch({
   *   query: 'Experienced backend developer',
   *   vacancy_id: 'vacancy-uuid',
   *   min_semantic_score: 0.7,
   *   limit: 20
   * });
   *
   * // Search with traditional filters
   * const results = await semanticSearchClient.semanticSearch({
   *   query: 'Senior software engineer',
   *   filters: {
   *     min_experience_years: 5,
   *     location: 'Remote'
   *   },
   *   semantic_weight: 0.8,
   *   keyword_weight: 0.2
   * });
   * ```
   */
  async semanticSearch(request: SemanticSearchRequest): Promise<SemanticSearchResponse> {
    try {
      const response: AxiosResponse<SemanticSearchResponse> = await this.client.post(
        '/api/semantic-search/candidates',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Semantic search using GET request with query parameters
   *
   * Alternative to POST endpoint that uses query parameters instead of JSON body.
   * Useful for simple searches and browser-based queries.
   *
   * @param params - Search parameters as query object
   * @returns Search results with candidate list and semantic scores
   * @throws ApiError if search fails
   *
   * @example
   * ```ts
   * // Simple semantic search
   * const results = await semanticSearchClient.semanticSearchGet({
   *   query: 'Find senior Python developers',
   *   limit: 10
   * });
   *
   * // Search with filters
   * const results = await semanticSearchClient.semanticSearchGet({
   *   query: 'Senior backend engineer',
   *   min_experience_years: 5,
   *   location: 'Remote',
   *   min_semantic_score: 0.7
   * });
   * ```
   */
  async semanticSearchGet(params: {
    query: string;
    vacancy_id?: string;
    min_semantic_score?: number;
    semantic_weight?: number;
    keyword_weight?: number;
    use_hybrid?: boolean;
    language?: string;
    skills?: string;
    min_experience_years?: number;
    max_experience_years?: number;
    location?: string;
    education_level?: string;
    skip?: number;
    limit?: number;
  }): Promise<SemanticSearchResponse> {
    try {
      const response: AxiosResponse<SemanticSearchResponse> = await this.client.get(
        '/api/semantic-search/candidates',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Hybrid search combining semantic and keyword matching
   *
   * Provides the best of both worlds: semantic understanding using LLM-powered
   * natural language processing combined with traditional keyword matching.
   *
   * @param request - Hybrid search request with query, weights, and optional filters
   * @returns Search results with both semantic and keyword scores
   * @throws ApiError if search fails
   *
   * @example
   * ```ts
   * // Balanced hybrid search
   * const results = await semanticSearchClient.hybridSearch({
   *   query: 'React developer with TypeScript',
   *   semantic_weight: 0.6,
   *   keyword_weight: 0.4,
   *   limit: 10
   * });
   *
   * // Semantic-focused search with filters
   * const results = await semanticSearchClient.hybridSearch({
   *   query: 'Senior Python backend engineer',
   *   semantic_weight: 0.8,
   *   keyword_weight: 0.2,
   *   filters: {
   *     min_experience_years: 5,
   *     location: 'Remote'
   *   },
   *   limit: 20
   * });
   *
   * // Keyword-focused search
   * const results = await semanticSearchClient.hybridSearch({
   *   query: 'Java Spring developer',
   *   semantic_weight: 0.3,
   *   keyword_weight: 0.7,
   *   filters: {
   *     skills: ['Java', 'Spring', 'PostgreSQL']
   *   }
   * });
   * ```
   */
  async hybridSearch(request: HybridSearchRequest): Promise<HybridSearchResponse> {
    try {
      const response: AxiosResponse<HybridSearchResponse> = await this.client.post(
        '/api/semantic-search/hybrid',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get detailed explanation of why a resume matches a query (POST endpoint)
   *
   * Provides semantic match explanations showing:
   * - Overall semantic similarity score
   * - Skill match score with matched/inferred/missing skills
   * - Experience relevance score
   * - Context fit score
   * - Human-readable explanation of the match
   *
   * @param request - Match explanation request with query and resume_id
   * @returns Detailed match explanation
   * @throws ApiError if explanation generation fails
   *
   * @example
   * ```ts
   * // Get match explanation
   * const explanation = await semanticSearchClient.explainMatch({
   *   query: 'Find senior Python developers with leadership experience',
   *   resume_id: 'resume-uuid'
   * });
   *
   * // With vacancy context
   * const explanation = await semanticSearchClient.explainMatch({
   *   query: 'Backend engineer',
   *   resume_id: 'resume-uuid',
   *   vacancy_id: 'vacancy-uuid'
   * });
   * ```
   */
  async explainMatch(request: MatchExplanationRequest): Promise<MatchExplanationResponse> {
    try {
      const response: AxiosResponse<MatchExplanationResponse> = await this.client.post(
        '/api/semantic-search/explain',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get detailed explanation of why a resume matches a query (GET endpoint)
   *
   * Alternative to POST endpoint using URL parameters. Useful for
   * simple queries and browser-based access.
   *
   * @param resume_id - Resume UUID to explain
   * @param params - Query parameters including the search query
   * @returns Detailed match explanation
   * @throws ApiError if explanation generation fails
   *
   * @example
   * ```ts
   * // Get match explanation
   * const explanation = await semanticSearchClient.explainMatchGet(
   *   'resume-uuid',
   *   { query: 'Senior Python developer with leadership experience' }
   * );
   *
   * // With vacancy context
   * const explanation = await semanticSearchClient.explainMatchGet(
   *   'resume-uuid',
   *   {
   *     query: 'Backend engineer',
   *     vacancy_id: 'vacancy-uuid'
   *   }
   * );
   * ```
   */
  async explainMatchGet(
    resume_id: string,
    params: {
      query: string;
      vacancy_id?: string;
    }
  ): Promise<MatchExplanationResponse> {
    try {
      const response: AxiosResponse<MatchExplanationResponse> = await this.client.get(
        `/api/semantic-search/explain/${resume_id}`,
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

/**
 * Default semantic search client instance
 */
export const semanticSearchClient = new SemanticSearchClient();
