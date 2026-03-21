/**
 * Analytics API Client
 *
 * Этот модуль предоставляет клиент для работы с аналитикой через микросервис Analytics Service.
 * Поддерживает получение метрик использования API, AI объяснимости, трендов производительности моделей.
 *
 * @example
 * ```ts
 * import { analyticsClient, AnalyticsClient } from '@/api/analytics';
 *
 * // Получение аналитики использования API
 * const apiUsage = await analyticsClient.getAPIUsageAnalytics();
 *
 * // Получение важности фичей модели
 * const importance = await analyticsClient.getFeatureImportance();
 *
 * // Получение объяснения ранжирования кандидата
 * const rationale = await analyticsClient.getRankingRationale('candidate-uuid');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';

/**
 * API request status
 */
export enum APIRequestStatus {
  Success = 'success',
  RateLimited = 'rate_limited',
  Unauthorized = 'unauthorized',
  Forbidden = 'forbidden',
  NotFound = 'not_found',
  ServerError = 'server_error',
  ValidationError = 'validation_error',
}

/**
 * API usage metrics summary
 */
export interface APIUsageSummary {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  rate_limited_requests: number;
  average_response_time_ms: number;
  p95_response_time_ms: number;
  p99_response_time_ms: number;
  unique_endpoints: number;
  date_range: {
    start_date: string;
    end_date: string;
  };
}

/**
 * Request count by time period
 */
export interface RequestCountByTime {
  timestamp: string;
  count: number;
  success_count: number;
  error_count: number;
}

/**
 * Response time metrics
 */
export interface ResponseTimeMetrics {
  timestamp: string;
  average_ms: number;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
}

/**
 * Endpoint usage statistics
 */
export interface EndpointUsage {
  endpoint: string;
  method: string;
  request_count: number;
  success_count: number;
  error_count: number;
  average_response_time_ms: number;
  error_rate: number;
}

/**
 * Status code distribution
 */
export interface StatusCodeDistribution {
  status_code: number;
  count: number;
  percentage: number;
}

/**
 * Top errors by frequency
 */
export interface TopError {
  status_code: number;
  endpoint: string;
  method: string;
  count: number;
  last_occurred: string;
}

/**
 * API usage analytics response
 */
export interface APIUsageAnalytics {
  summary: APIUsageSummary;
  requests_by_time: RequestCountByTime[];
  response_times: ResponseTimeMetrics[];
  top_endpoints: EndpointUsage[];
  status_codes: StatusCodeDistribution[];
  top_errors: TopError[];
}

// ==================== AI Explainability Types ====================

/**
 * Confidence interval for model predictions
 */
export interface ConfidenceIntervalStats {
  lower: number;
  upper: number;
  confidence_level: number;
}

/**
 * Confidence distribution counts
 */
export interface ConfidenceDistribution {
  high_confidence_count: number;
  medium_confidence_count: number;
  low_confidence_count: number;
}

/**
 * Model confidence response
 */
export interface ModelConfidenceResponse {
  average_confidence: number;
  confidence_interval: ConfidenceIntervalStats;
  distribution: ConfidenceDistribution;
  confidence_accuracy_correlation: number;
}

/**
 * Feature importance item - matches API response structure
 */
export interface FeatureImportanceItem {
  feature_name: string;
  importance_score: number;
  rank: number;
  description: string;
  category: string;
}

/**
 * Feature importance response - matches API response structure
 */
export interface FeatureImportanceResponse {
  features: FeatureImportanceItem[];
  model_version: string;
  model_type: string;
  total_features: number;
  last_updated: string;
}

/**
 * Ranking factor detail - matches API RankingFactorDetail structure
 */
export interface RankingFactorDetail {
  factor_name: string;
  score: number;
  weight: number;
  contribution: number;
  description: string;
  raw_value?: number;
}

/**
 * Skills match detail - matches API SkillsMatchDetail structure
 */
export interface SkillsMatchDetail {
  matched_skills: string[];
  missing_skills: string[];
  additional_skills: string[];
  match_percentage: number;
}

/**
 * Ranking rationale response - matches API response structure
 */
export interface RankingRationaleResponse {
  candidate_id: string;
  vacancy_id?: string;
  rank_score: number;
  rank_position?: number;
  recommendation: 'excellent' | 'good' | 'maybe' | 'poor';
  confidence: number;
  model_version: string;
  model_type: string;
  factors: RankingFactorDetail[];
  skills_match?: SkillsMatchDetail;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  generated_at: string;
}

/**
 * Performance metrics for a single time point - matches API data_points structure
 */
export interface PerformanceMetricPoint {
  timestamp: string;
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  sample_count: number;
}

/**
 * Model performance trend - matches API models array structure
 */
export interface ModelPerformanceTrend {
  model_name: string;
  model_version: string;
  current_accuracy: number;
  current_f1_score: number;
  trend_direction: 'improving' | 'stable' | 'declining';
  trend_change_pct: number;
  data_points: PerformanceMetricPoint[];
  alert_status?: string | null;
}

/**
 * Performance trends response - matches API response structure
 */
export interface PerformanceTrendsResponse {
  period: string;
  start_date: string;
  end_date: string;
  models: ModelPerformanceTrend[];
  overall_trend: 'improving' | 'stable' | 'declining';
  total_evaluations: number;
}

// ==================== Recruiting Analytics Types ====================

/**
 * Funnel stage metrics - matches API FunnelStageMetrics structure
 */
export interface FunnelStageMetrics {
  stage_name: string;
  count: number;
  conversion_rate_from_previous: number | null;
  conversion_rate_from_start: number;
}

/**
 * Funnel metrics response - matches API FunnelMetricsResponse structure
 */
export interface FunnelMetricsResponse {
  stages: FunnelStageMetrics[];
  total_candidates: number;
}

/**
 * Source metrics - matches API SourceMetrics structure
 */
export interface SourceMetrics {
  source: string;
  candidate_count: number;
  conversion_rate: number;
  hired_count: number;
}

/**
 * Source tracking response - matches API SourceTrackingResponse structure
 */
export interface SourceTrackingResponse {
  sources: SourceMetrics[];
  total_candidates: number;
}

/**
 * Recruiter metrics - matches API RecruiterMetrics structure
 */
export interface RecruiterMetrics {
  recruiter_id: string;
  recruiter_name: string;
  resumes_processed: number;
  interviews_conducted: number;
  hires: number;
  placement_rate: number;
  average_time_to_hire_days: number;
}

/**
 * Recruiter performance response - matches API RecruiterPerformanceResponse structure
 */
export interface RecruiterPerformanceResponse {
  recruiters: RecruiterMetrics[];
  period_start: string | null;
  period_end: string | null;
  total_recruiters: number;
}

/**
 * Конфигурация по умолчанию для клиента аналитики
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с аналитикой
 *
 * Предоставляет методы для получения аналитики использования API,
 * AI объяснимости и метрик производительности с proper
 * обработкой ошибок и типобезопасностью.
 */
export class AnalyticsClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента аналитики
   *
   * @param config - Опциональные переопределения конфигурации
   */
  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Интерцептор ответов для обработки ошибок
    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(this.transformError(error))
    );
  }

  /**
   * Получение аналитики использования API
   *
   * @param startDate - Опциональная дата начала для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная дата окончания для фильтрации (формат ISO 8601)
   * @param interval - Интервал времени для агрегации (hour, day, week)
   * @returns Данные аналитики использования API
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * const analytics = await analyticsClient.getAPIUsageAnalytics();
   * ```
   *
   * @example
   * ```ts
   * const analytics = await analyticsClient.getAPIUsageAnalytics(
   *   '2024-01-01',
   *   '2024-12-31',
   *   'day'
   * );
   * ```
   */
  async getAPIUsageAnalytics(
    startDate?: string,
    endDate?: string,
    interval: 'hour' | 'day' | 'week' = 'day'
  ): Promise<APIUsageAnalytics> {
    try {
      const params: Record<string, string> = { interval };
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<APIUsageAnalytics> = await this.client.get(
        '/api/analytics/api-usage',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение сводки использования для конкретного API ключа
   *
   * @param apiKeyId - UUID API ключа
   * @param startDate - Опциональная дата начала для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная дата окончания для фильтрации (формат ISO 8601)
   * @returns Сводка использования API для ключа
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * const summary = await analyticsClient.getAPIKeyUsage('key-uuid');
   * ```
   */
  async getAPIKeyUsage(
    apiKeyId: string,
    startDate?: string,
    endDate?: string
  ): Promise<APIUsageSummary> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<APIUsageSummary> = await this.client.get(
        `/api/analytics/api-usage/keys/${apiKeyId}`,
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== AI Explainability Methods ====================

  /**
   * Получение статистики уверенности модели
   *
   * Возвращает распределение уверенности модели и статистику, включая
   * среднюю уверенность, доверительные интервалы и разбивку распределения.
   *
   * @returns Статистика уверенности модели
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * const confidence = await analyticsClient.getModelConfidence();
   * console.log(`Average: ${confidence.average_confidence}`);
   * console.log(`High confidence: ${confidence.distribution.high_confidence_count}`);
   * ```
   */
  async getModelConfidence(): Promise<ModelConfidenceResponse> {
    try {
      const response: AxiosResponse<ModelConfidenceResponse> = await this.client.get(
        '/api/analytics/ai-explainability/confidence'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение важности фичей из обученной модели
   *
   * Возвращает оценки важности фичей для всех фичей ранжирования,
   * показывая какие факторы больше всего влияют на ранжирование кандидатов.
   *
   * @returns Данные важности фичей с описаниями
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * const importance = await analyticsClient.getFeatureImportance();
   * importance.features.forEach(f => {
   *   console.log(`${f.feature_name}: ${(f.importance_score * 100).toFixed(1)}%`);
   * });
   * ```
   */
  async getFeatureImportance(): Promise<FeatureImportanceResponse> {
    try {
      const response: AxiosResponse<FeatureImportanceResponse> = await this.client.get(
        '/api/analytics/ai-explainability/feature-importance'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение обоснования ранжирования для конкретного кандидата
   *
   * Предоставляет детальное объяснение того, почему кандидат получил свой ранг,
   * включая вклады фичей, сильные и слабые стороны, и доверительный интервал.
   *
   * @param candidateId - UUID кандидата
   * @returns Детальное обоснование ранжирования
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * const rationale = await analyticsClient.getRankingRationale('candidate-uuid');
   * console.log(`Score: ${rationale.rank_score}`);
   * console.log(`Summary: ${rationale.summary}`);
   * ```
   */
  async getRankingRationale(candidateId: string): Promise<RankingRationaleResponse> {
    try {
      const response: AxiosResponse<RankingRationaleResponse> = await this.client.get(
        `/api/analytics/ai-explainability/ranking-rationale/${candidateId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение трендов производительности модели во времени
   *
   * Возвращает временные ряды метрик производительности (точность, F1, NDCG) с
   * анализом трендов и агрегированной статистикой.
   *
   * @param period - Период времени для анализа ("7d", "30d", или "90d")
   * @param startDate - Опциональная дата начала для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная дата окончания для фильтрации (формат ISO 8601)
   * @returns Тренды производительности с метриками и агрегатами
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * const trends = await analyticsClient.getPerformanceTrends('30d');
   * console.log(`Overall Trend: ${trends.overall_trend}`);
   * trends.models.forEach(m => {
   *   console.log(`${m.model_name}: accuracy=${m.current_accuracy}, f1=${m.current_f1_score}`);
   * });
   * ```
   */
  async getPerformanceTrends(
    period: '7d' | '30d' | '90d' = '30d',
    startDate?: string,
    endDate?: string
  ): Promise<PerformanceTrendsResponse> {
    try {
      const params: Record<string, string> = { period };
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<PerformanceTrendsResponse> = await this.client.get(
        '/api/analytics/ai-explainability/performance-trends',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Recruiting Analytics Methods ====================

  /**
   * Получение метрик визуализации воронки найма
   *
   * Возвращает метрики воронки найма, показывая количество кандидатов
   * на каждом этапе и коэффициенты конверсии между этапами.
   *
   * @param startDate - Опциональная дата начала для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная дата окончания для фильтрации (формат ISO 8601)
   * @returns Метрики воронки с количеством этапов и коэффициентами конверсии
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * const funnel = await analyticsClient.getFunnelMetrics();
   * console.log(`Total candidates: ${funnel.total_candidates}`);
   * funnel.stages.forEach(s => {
   *   console.log(`${s.stage_name}: ${s.count} (${(s.conversion_rate_from_start * 100).toFixed(1)}%)`);
   * });
   * ```
   */
  async getFunnelMetrics(
    startDate?: string,
    endDate?: string
  ): Promise<FunnelMetricsResponse> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<FunnelMetricsResponse> = await this.client.get(
        '/api/analytics/funnel',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение аналитики отслеживания источников кандидатов
   *
   * Возвращает аналитику о том, откуда приходят кандидаты, включая
   * источники, такие как рефералы, LinkedIn, сайт компании и т.д.
   * Для каждого источника отслеживается количество кандидатов и коэффициенты конверсии.
   *
   * @param startDate - Опциональная дата начала для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная дата окончания для фильтрации (формат ISO 8601)
   * @returns Метрики источников с количеством кандидатов и коэффициентами конверсии
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * const sources = await analyticsClient.getSourceTracking();
   * console.log(`Total candidates: ${sources.total_candidates}`);
   * sources.sources.forEach(s => {
   *   console.log(`${s.source}: ${s.candidate_count} candidates, ${(s.conversion_rate * 100).toFixed(1)}% conversion`);
   * });
   * ```
   */
  async getSourceTracking(
    startDate?: string,
    endDate?: string
  ): Promise<SourceTrackingResponse> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<SourceTrackingResponse> = await this.client.get(
        '/api/analytics/source-tracking',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение метрик производительности рекрутеров
   *
   * Возвращает метрики производительности для рекрутеров, включая обработанных
   * кандидатов, проведенные интервью, нанятых сотрудников и процент трудоустройства.
   *
   * @param startDate - Опциональная дата начала для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная дата окончания для фильтрации (формат ISO 8601)
   * @param limit - Количество рекрутеров для возврата (по умолчанию 10, максимум 100)
   * @returns Метрики производительности рекрутеров
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * const performance = await analyticsClient.getRecruiterPerformance();
   * console.log(`Total recruiters: ${performance.total_recruiters}`);
   * performance.recruiters.forEach(r => {
   *   console.log(`${r.recruiter_name}: ${r.hires} hires, ${(r.placement_rate * 100).toFixed(1)}% placement rate`);
   * });
   * ```
   */
  async getRecruiterPerformance(
    startDate?: string,
    endDate?: string,
    limit: number = 10
  ): Promise<RecruiterPerformanceResponse> {
    try {
      const params: Record<string, string | number> = { limit };
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<RecruiterPerformanceResponse> = await this.client.get(
        '/api/analytics/recruiter-performance',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Преобразование ошибки Axios в стандартизированную ошибку API
   *
   * @param error - Ошибка Axios
   * @returns Преобразованная ошибка API
   */
  private transformError(error: unknown): ApiError {
    const axiosError = error as AxiosError<{ detail?: string }>;

    // Ошибка сети (нет ответа)
    if (!axiosError.response) {
      if (axiosError.code === 'ECONNABORTED') {
        return {
          detail: 'Таймаут запроса. Проверьте соединение и попробуйте снова.',
          status: 408,
        };
      }
      return {
        detail: 'Ошибка сети. Проверьте соединение и попробуйте снова.',
        status: 0,
      };
    }

    // Сервер вернул ошибку
    const status = axiosError.response.status;
    const data = axiosError.response.data;

    // Используем сообщение об ошибке от сервера, если доступно
    if (data?.detail) {
      return { detail: data.detail, status };
    }

    // Сообщения об ошибках по умолчанию для разных кодов статуса
    const defaultMessages: Record<number, string> = {
      400: 'Неверный запрос. Проверьте введенные данные.',
      401: 'Не авторизован. Войдите в систему.',
      403: 'Доступ запрещен. У вас нет прав для выполнения этого действия.',
      404: 'Данные не найдены.',
      422: 'Ошибка валидации. Проверьте введенные данные.',
      429: 'Слишком много запросов. Попробуйте позже.',
      500: 'Ошибка сервера. Попробуйте позже.',
      502: 'Ошибка шлюза. Попробуйте позже.',
      503: 'Сервис недоступен. Попробуйте позже.',
    };

    return {
      detail: data?.detail || defaultMessages[status] || 'Произошла непредвиденная ошибка.',
      status,
    };
  }
}

/**
 * Экземпляр клиента аналитики по умолчанию
 */
export const analyticsClient = new AnalyticsClient();
