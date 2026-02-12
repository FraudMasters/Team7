/**
 * Salary Benchmarking and Compensation Analysis API Client
 *
 * This module provides a convenient interface for salary benchmarking,
 * compensation analysis, offer comparison, and equity analysis.
 *
 * @example
 * ```ts
 * import { salaryBenchmarking } from '@/api/salaryBenchmarking';
 *
 * // Get salary benchmarks
 * const benchmarks = await salaryBenchmarking.getBenchmarks({
 *   role: 'Senior React Developer',
 *   location: 'San Francisco, CA',
 *   experience_level: 'senior',
 * });
 *
 * // Get salary suggestion for candidate
 * const suggestion = await salaryBenchmarking.getSuggestion({
 *   resume_id: 'abc123',
 *   vacancy_id: 'vacancy-1',
 *   include_cost_of_living: true,
 * });
 *
 * // Create salary history record
 * const history = await salaryBenchmarking.createSalaryHistory({
 *   resume_id: 'abc123',
 *   salary_amount: 95000,
 *   currency: 'USD',
 *   effective_date: '2024-01-01',
 * });
 *
 * // Compare offers
 * const comparison = await salaryBenchmarking.compareOffers({
 *   resume_id: 'abc123',
 *   offers: [
 *     { salary: 100000, location: 'New York' },
 *     { salary: 95000, location: 'Austin' },
 *   ],
 * });
 *
 * // Get equity analysis
 * const equity = await salaryBenchmarking.getEquityAnalysis({
 *   vacancy_id: 'vacancy-1',
 *   include_demographics: true,
 * });
 * ```
 */

import axios, { AxiosInstance } from 'axios';
import type {
  SalaryBenchmarkRequest,
  SalaryBenchmarkResponse,
  SalarySuggestionRequest,
  SalarySuggestionResponse,
  SalaryHistoryCreate,
  SalaryHistoryResponse,
  SalaryHistoryListResponse,
  OfferComparisonRequest,
  OfferComparisonResponse,
  EquityAnalysisRequest,
  EquityAnalysisResponse,
  MarketTrendsResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 120000,
};

/**
 * Transform Axios error to standardized API error
 */
function transformError(error: unknown): ApiError {
  const axiosError = error as {
    response?: { status?: number; data?: { detail?: string } };
    message?: string;
  };

  return {
    detail: axiosError.response?.data?.detail ?? axiosError.message ?? 'Unknown error',
    status: axiosError.response?.status,
  };
}

/**
 * Salary Benchmarking Client class
 *
 * Provides methods for salary benchmarks, suggestions, history tracking,
 * offer comparison, and equity analysis.
 */
export class SalaryBenchmarkingClient {
  private client: AxiosInstance;

  /**
   * Create a new Salary Benchmarking client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);
  }

  /**
   * Get the underlying axios instance for custom requests
   *
   * @returns Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }

  /**
   * Get salary benchmarks for a role and location
   *
   * @param request - Salary benchmark request
   * @returns Salary benchmark data
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const benchmarks = await salaryBenchmarking.getBenchmarks({
   *   role: 'Senior React Developer',
   *   location: 'San Francisco, CA',
   *   experience_level: 'senior',
   *   country: 'US',
   *   industry: 'Technology',
   * });
   * ```
   */
  async getBenchmarks(request: SalaryBenchmarkRequest): Promise<SalaryBenchmarkResponse> {
    try {
      const params = new URLSearchParams();

      params.append('role', request.role);
      params.append('location', request.location);

      if (request.country) params.append('country', request.country);
      if (request.experience_level) params.append('experience_level', request.experience_level);
      if (request.industry) params.append('industry', request.industry);
      if (request.employment_type) params.append('employment_type', request.employment_type);

      const queryString = params.toString();
      const url = `/api/salary-benchmarking/benchmarks?${queryString}`;

      const response = await this.client.get<SalaryBenchmarkResponse>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get salary suggestion for a candidate for a specific vacancy
   *
   * @param request - Salary suggestion request
   * @returns Suggested salary range with confidence level
   * @throws ApiError if suggestion fails
   *
   * @example
   * ```ts
   * const suggestion = await salaryBenchmarking.getSuggestion({
   *   resume_id: 'abc123',
   *   vacancy_id: 'vacancy-1',
   *   include_cost_of_living: true,
   *   target_location: 'Remote',
   * });
   * ```
   */
  async getSuggestion(request: SalarySuggestionRequest): Promise<SalarySuggestionResponse> {
    try {
      const response = await this.client.post<SalarySuggestionResponse>(
        '/api/salary-benchmarking/suggestions',
        request
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Create a new salary history record
   *
   * @param request - Salary history creation request
   * @returns Created salary history record
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const history = await salaryBenchmarking.createSalaryHistory({
   *   resume_id: 'abc123',
   *   salary_amount: 95000,
   *   currency: 'USD',
   *   effective_date: '2024-01-01',
   *   salary_type: 'current',
   *   employment_type: 'full_time',
   *   job_title: 'Software Developer',
   *   company_name: 'Acme Corp',
   *   location: 'New York, NY',
   * });
   * ```
   */
  async createSalaryHistory(request: SalaryHistoryCreate): Promise<SalaryHistoryResponse> {
    try {
      const response = await this.client.post<SalaryHistoryResponse>(
        '/api/salary-benchmarking/salary-history',
        request
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get salary history for a candidate
   *
   * @param resumeId - Resume UUID
   * @param options - Optional query parameters
   * @returns List of salary history records
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const history = await salaryBenchmarking.getSalaryHistory('abc123', {
   *   skip: 0,
   *   limit: 10,
   * });
   * ```
   */
  async getSalaryHistory(
    resumeId: string,
    options?: {
      skip?: number;
      limit?: number;
      salary_type?: string;
    }
  ): Promise<SalaryHistoryListResponse> {
    try {
      const params = new URLSearchParams();

      if (options?.skip !== undefined) params.append('skip', String(options.skip));
      if (options?.limit !== undefined) params.append('limit', String(options.limit));
      if (options?.salary_type) params.append('salary_type', options.salary_type);

      const queryString = params.toString();
      const url = `/api/salary-benchmarking/salary-history/${resumeId}${queryString ? `?${queryString}` : ''}`;

      const response = await this.client.get<SalaryHistoryListResponse>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Compare multiple job offers with cost-of-living adjustments
   *
   * @param request - Offer comparison request
   * @returns Comparison analysis with recommendation
   * @throws ApiError if comparison fails
   *
   * @example
   * ```ts
   * const comparison = await salaryBenchmarking.compareOffers({
   *   resume_id: 'abc123',
   *   offers: [
   *     {
   *       salary: 100000,
   *       location: 'New York, NY',
   *       currency: 'USD',
   *       bonus: 10000,
   *       equity: 5000,
   *       job_title: 'Senior Developer',
   *       company: 'Tech Corp',
   *     },
   *     {
   *       salary: 95000,
   *       location: 'Austin, TX',
   *       currency: 'USD',
   *       bonus: 8000,
   *       job_title: 'Senior Developer',
   *       company: 'Startup Inc',
   *     },
   *   ],
   *   apply_cost_of_living: true,
   * });
   * ```
   */
  async compareOffers(request: OfferComparisonRequest): Promise<OfferComparisonResponse> {
    try {
      const response = await this.client.post<OfferComparisonResponse>(
        '/api/salary-benchmarking/compare-offers',
        request
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get equity analysis for a vacancy
   *
   * @param request - Equity analysis request
   * @returns Equity analysis with disparities and recommendations
   * @throws ApiError if analysis fails
   *
   * @example
   * ```ts
   * const equity = await salaryBenchmarking.getEquityAnalysis({
   *   vacancy_id: 'vacancy-1',
   *   include_demographics: true,
   *   pay_gap_threshold: 0.05,
   * });
   * ```
   */
  async getEquityAnalysis(request: EquityAnalysisRequest): Promise<EquityAnalysisResponse> {
    try {
      const params = new URLSearchParams();

      if (request.include_demographics !== undefined) {
        params.append('include_demographics', String(request.include_demographics));
      }
      if (request.pay_gap_threshold !== undefined) {
        params.append('pay_gap_threshold', String(request.pay_gap_threshold));
      }

      const queryString = params.toString();
      const url = `/api/salary-benchmarking/equity-analysis?${queryString}`;

      const response = await this.client.get<EquityAnalysisResponse>(url, {
        params: { vacancy_id: request.vacancy_id },
      });
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get market trends for a role and location over time
   *
   * @param request - Market trends request
   * @returns Market trends data with historical salary changes
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const trends = await salaryBenchmarking.getMarketTrends({
   *   role: 'Senior React Developer',
   *   location: 'San Francisco, CA',
   *   period_type: 'quarterly',
   *   periods: 8,
   * });
   * ```
   */
  async getMarketTrends(request: {
    role: string;
    location: string;
    country?: string;
    period_type?: string;
    periods?: number;
  }): Promise<MarketTrendsResponse> {
    try {
      const params = new URLSearchParams();

      params.append('role', request.role);
      params.append('location', request.location);

      if (request.country) params.append('country', request.country);
      if (request.period_type) params.append('period_type', request.period_type);
      if (request.periods) params.append('periods', String(request.periods));

      const queryString = params.toString();
      const url = `/api/salary-benchmarking/market-trends?${queryString}`;

      const response = await this.client.get<MarketTrendsResponse>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }
}

/**
 * Default singleton instance of the Salary Benchmarking client
 */
export const salaryBenchmarking = new SalaryBenchmarkingClient();
