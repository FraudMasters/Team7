/**
 * Skill Gap Analysis API Client
 *
 * This module provides a convenient interface for analyzing skill gaps
 * between candidates and job vacancies, and getting personalized learning
 * recommendations.
 *
 * @example
 * ```ts
 * import { skillGap } from '@/api/skillGap';
 *
 * // Analyze skill gaps
 * const analysis = await skillGap.analyze({
 *   resume_id: 'abc123',
 *   vacancy_data: {
 *     id: 'vacancy-1',
 *     title: 'Senior React Developer',
 *     required_skills: ['React', 'TypeScript', 'Node.js'],
 *   },
 * });
 *
 * // Get learning recommendations
 * const recommendations = await skillGap.getRecommendations({
 *   skills: ['React', 'TypeScript'],
 *   max_cost_per_resource: 50,
 * });
 * ```
 */

import axios, { AxiosInstance } from 'axios';
import type {
  SkillGapAnalysisRequest,
  SkillGapAnalysisResponse,
  LearningRecommendationsRequest,
  LearningRecommendationsResponse,
  LearningResourcesQuery,
  LearningResourcesListResponse,
  SkillGapReportListResponse,
  ApiError,
} from '@/types/api';

/**
 * Default API configuration
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
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
 * Skill Gap Analysis Client class
 *
 * Provides methods for skill gap analysis and learning recommendations.
 */
export class SkillGapClient {
  private client: AxiosInstance;

  /**
   * Create a new Skill Gap client instance
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
   * Analyze skill gaps between a candidate and job vacancy
   *
   * @param request - Skill gap analysis request
   * @returns Skill gap analysis results
   * @throws ApiError if analysis fails
   *
   * @example
   * ```ts
   * const analysis = await skillGap.analyze({
   *   resume_id: 'abc123',
   *   vacancy_data: {
   *     id: 'vacancy-1',
   *     title: 'Senior React Developer',
   *     description: 'Looking for React developer...',
   *     required_skills: ['React', 'TypeScript', 'Node.js'],
   *     required_skill_levels: {
   *       'React': 'advanced',
   *       'TypeScript': 'intermediate',
   *     },
   *   },
   * });
   * ```
   */
  async analyze(request: SkillGapAnalysisRequest): Promise<SkillGapAnalysisResponse> {
    try {
      const response = await this.client.post<SkillGapAnalysisResponse>(
        '/api/skill-gap/analyze',
        request
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get learning recommendations for specified skills
   *
   * @param request - Learning recommendations request
   * @returns Personalized learning recommendations
   * @throws ApiError if recommendation fails
   *
   * @example
   * ```ts
   * const recommendations = await skillGap.getRecommendations({
   *   skills: ['React', 'TypeScript', 'Docker'],
   *   skill_levels: {
   *     'React': 'advanced',
   *     'TypeScript': 'intermediate',
   *   },
   *   max_recommendations_per_skill: 3,
   *   max_cost_per_resource: 50,
   *   include_free_resources: true,
   *   min_rating: 4.0,
   * });
   * ```
   */
  async getRecommendations(
    request: LearningRecommendationsRequest
  ): Promise<LearningRecommendationsResponse> {
    try {
      const response = await this.client.post<LearningRecommendationsResponse>(
        '/api/skill-gap/learning-resources/recommendations',
        {
          skills: request.skills,
          skill_levels: request.skill_levels,
          max_recommendations_per_skill: request.max_recommendations_per_skill ?? 5,
          max_cost_per_resource: request.max_cost_per_resource,
          include_free_resources: request.include_free_resources ?? true,
          min_rating: request.min_rating ?? 0.0,
          preferred_languages: request.preferred_languages ?? ['en'],
        }
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get skill gap reports for a specific resume
   *
   * @param resumeId - Resume ID
   * @returns List of skill gap reports
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const reports = await skillGap.getReports('resume-123');
   * ```
   */
  async getReports(resumeId: string): Promise<SkillGapReportListResponse> {
    try {
      const response = await this.client.get<SkillGapReportListResponse>(
        `/api/skill-gap/reports/${resumeId}`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get a specific skill gap report by ID
   *
   * @param reportId - Report ID
   * @returns Skill gap report details
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const report = await skillGap.getReport('report-123');
   * ```
   */
  async getReport(reportId: string): Promise<SkillGapAnalysisResponse> {
    try {
      const response = await this.client.get<SkillGapAnalysisResponse>(
        `/api/skill-gap/reports/by-id/${reportId}`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Query learning resources with filters
   *
   * @param query - Query parameters for filtering resources
   * @returns Filtered learning resources
   * @throws ApiError if query fails
   *
   * @example
   * ```ts
   * const resources = await skillGap.queryResources({
   *   skill: 'React',
   *   resource_type: 'course',
   *   access_type: 'free',
   *   min_rating: 4.0,
   *   limit: 10,
   * });
   * ```
   */
  async queryResources(query: LearningResourcesQuery): Promise<LearningResourcesListResponse> {
    try {
      const params = new URLSearchParams();

      if (query.skill) params.append('skill', query.skill);
      if (query.resource_type) params.append('resource_type', query.resource_type);
      if (query.skill_level) params.append('skill_level', query.skill_level);
      if (query.access_type) params.append('access_type', query.access_type);
      if (query.min_rating) params.append('min_rating', query.min_rating.toString());
      if (query.max_cost) params.append('max_cost', query.max_cost.toString());
      if (query.limit) params.append('limit', query.limit.toString());
      if (query.offset) params.append('offset', query.offset.toString());

      const response = await this.client.get<LearningResourcesListResponse>(
        `/api/skill-gap/learning-resources?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get learning resources for a specific skill gap report
   *
   * @param reportId - Skill gap report ID
   * @returns Learning resources associated with the report
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const resources = await skillGap.getReportResources('report-123');
   * ```
   */
  async getReportResources(reportId: string): Promise<LearningResourcesListResponse> {
    try {
      const response = await this.client.get<LearningResourcesListResponse>(
        `/api/skill-gap/reports/${reportId}/resources`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get skill development plan for a candidate
   *
   * @param planId - Development plan ID
   * @returns Skill development plan details
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const plan = await skillGap.getDevelopmentPlan('plan-123');
   * ```
   */
  async getDevelopmentPlan(planId: string): Promise<unknown> {
    try {
      const response = await this.client.get(
        `/api/skill-gap/development-plans/${planId}`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Get skill development plans for a resume
   *
   * @param resumeId - Resume ID
   * @returns List of skill development plans
   * @throws ApiError if fetch fails
   *
   * @example
   * ```ts
   * const plans = await skillGap.getDevelopmentPlans('resume-123');
   * ```
   */
  async getDevelopmentPlans(resumeId: string): Promise<unknown> {
    try {
      const response = await this.client.get(
        `/api/skill-gap/development-plans/resume/${resumeId}`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Analyze skill gaps and get recommendations in one call
   *
   * This is a convenience method that combines analyze() and getRecommendations()
   *
   * @param request - Skill gap analysis request
   * @param options - Optional recommendation settings
   * @returns Combined analysis and recommendations
   * @throws ApiError if analysis or recommendations fail
   *
   * @example
   * ```ts
   * const result = await skillGap.analyzeWithRecommendations({
   *   resume_id: 'abc123',
   *   vacancy_data: {
   *     id: 'vacancy-1',
   *     title: 'Senior React Developer',
   *     required_skills: ['React', 'TypeScript'],
   *   },
   * }, {
   *   max_cost_per_resource: 50,
   *   include_free_resources: true,
   * });
   * ```
   */
  async analyzeWithRecommendations(
    request: SkillGapAnalysisRequest,
    options: Partial<LearningRecommendationsRequest> = {}
  ): Promise<{
    analysis: SkillGapAnalysisResponse;
    recommendations: LearningRecommendationsResponse;
  }> {
    const analysis = await this.analyze(request);

    // Get recommendations for missing skills
    const skillsToLearn = analysis.missing_skills.length > 0
      ? analysis.missing_skills
      : analysis.partial_match_skills;

    const recommendations = skillsToLearn.length > 0
      ? await this.getRecommendations({
          skills: skillsToLearn,
          skill_levels: request.vacancy_data.required_skill_levels,
          ...options,
        })
      : {
          target_skills: [],
          recommendations: {},
          total_recommendations: 0,
          total_cost: 0,
          total_duration_hours: 0,
          alternative_free_resources: 0,
          skills_with_certifications: [],
          priority_ordering: [],
          summary: 'No skill gaps found - all requirements met!',
        };

    return { analysis, recommendations };
  }
}

/**
 * Default skill gap client instance
 *
 * Use this singleton instance for all skill gap API calls.
 */
export const skillGap = new SkillGapClient();

/**
 * Export skill gap client class for custom instances
 */
export default SkillGapClient;
