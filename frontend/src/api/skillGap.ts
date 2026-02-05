/**
 * Skill Gap Analysis API Client
 *
 * Этот модуль предоставляет удобный интерфейс для анализа разрыва в навыках
 * между кандидатами и вакансиями, а также получения персонализированных рекомендаций по обучению.
 *
 * @example
 * ```ts
 * import { skillGap } from '@/api/skillGap';
 *
 * // Анализ разрыва в навыках
 * const analysis = await skillGap.analyze({
 *   resume_id: 'abc123',
 *   vacancy_data: {
 *     id: 'vacancy-1',
 *     title: 'Senior React Developer',
 *     required_skills: ['React', 'TypeScript', 'Node.js'],
 *   },
 * });
 *
 * // Получение рекомендаций по обучению
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
 * Конфигурация API по умолчанию
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 120000,
};

/**
 * Преобразование ошибки Axios в стандартизированную ошибку API
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
 * Класс клиента анализа разрыва в навыках
 *
 * Предоставляет методы для анализа разрыва в навыках и рекомендаций по обучению.
 */
export class SkillGapClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента анализа разрыва в навыках
   *
   * @param config - Опциональные переопределения конфигурации
   */
  constructor(config = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);
  }

  /**
   * Получение базового экземпляра axios для кастомных запросов
   *
   * @returns Экземпляр Axios
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }

  /**
   * Анализ разрыва в навыках между кандидатом и вакансией
   *
   * @param request - Запрос на анализ разрыва в навыках
   * @returns Результаты анализа разрыва в навыках
   * @throws ApiError если анализ не удался
   *
   * @example
   * ```ts
   * const analysis = await skillGap.analyze({
   *   resume_id: 'abc123',
   *   vacancy_data: {
   *     id: 'vacancy-1',
   *     title: 'Senior React Developer',
   *     description: 'Ищем разработчика React...',
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
   * Получение рекомендаций по обучению для указанных навыков
   *
   * @param request - Запрос на рекомендации по обучению
   * @returns Персонализированные рекомендации по обучению
   * @throws ApiError если получение рекомендаций не удалось
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
   * Получение отчетов о разрыве в навыках для конкретного резюме
   *
   * @param resumeId - ID резюме
   * @returns Список отчетов о разрыве в навыках
   * @throws ApiError если получение не удалось
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
   * Получение конкретного отчета о разрыве в навыках по ID
   *
   * @param reportId - ID отчета
   * @returns Детали отчета о разрыве в навыках
   * @throws ApiError если получение не удалось
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
   * Поиск учебных ресурсов с фильтрами
   *
   * @param query - Параметры запроса для фильтрации ресурсов
   * @returns Отфильтрованные учебные ресурсы
   * @throws ApiError если поиск не удался
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
   * Получение учебных ресурсов для конкретного отчета о разрыве в навыках
   *
   * @param reportId - ID отчета о разрыве в навыках
   * @returns Учебные ресурсы, связанные с отчетом
   * @throws ApiError если получение не удалось
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
   * Получение плана развития навыков для кандидата
   *
   * @param planId - ID плана развития
   * @returns Детали плана развития навыков
   * @throws ApiError если получение не удалось
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
   * Получение планов развития навыков для резюме
   *
   * @param resumeId - ID резюме
   * @returns Список планов развития навыков
   * @throws ApiError если получение не удалось
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
   * Анализ разрыва в навыках и получение рекомендаций за один вызов
   *
   * Это удобный метод, объединяющий analyze() и getRecommendations()
   *
   * @param request - Запрос на анализ разрыва в навыках
   * @param options - Опциональные настройки рекомендаций
   * @returns Комбинированный анализ и рекомендации
   * @throws ApiError если анализ или рекомендации не удались
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

    // Получение рекомендаций для отсутствующих навыков
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
 * Экземпляр клиента анализа разрыва в навыках по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех вызовов API анализа разрыва в навыках.
 */
export const skillGap = new SkillGapClient();

/**
 * Экспорт класса клиента анализа разрыва в навыках для создания кастомных экземпляров
 */
export default SkillGapClient;
