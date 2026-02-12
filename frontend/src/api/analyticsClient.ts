/**
 * Analytics API Client
 *
 * Этот модуль предоставляет клиент для работы с аналитикой через микросервис Analytics Service.
 * Поддерживает получение метрик производительности, воронки найма, спроса на навыки,
 * отслеживания источников, показателей эффективности рекрутеров и экспорт данных.
 *
 * @example
 * ```ts
 * import { analyticsClient, AnalyticsClient } from '@/api/analyticsClient';
 *
 * // Получение ключевых метрик
 * const metrics = await analyticsClient.getKeyMetrics();
 *
 * // Получение метрик с фильтрацией по дате
 * const metrics = await analyticsClient.getKeyMetrics('2024-01-01', '2024-12-31');
 *
 * // Получение воронки найма
 * const funnel = await analyticsClient.getFunnelMetrics();
 *
 * // Получение спроса на навыки
 * const skills = await analyticsClient.getSkillDemand('2024-01-01', '2024-12-31', 30);
 *
 * // Получение отслеживания источников
 * const sources = await analyticsClient.getSourceTracking();
 *
 * // Получение эффективности рекрутеров
 * const recruiters = await analyticsClient.getRecruiterPerformance('2024-01-01', '2024-12-31', 10);
 *
 * // Экспорт аналитики в CSV
 * const blob = await analyticsClient.exportAnalytics({ format: 'csv' });
 *
 * // Экспорт аналитики в JSON с метаданными
 * const result = await analyticsClient.exportAnalyticsJson({
 *   start_date: '2024-01-01',
 *   end_date: '2024-12-31',
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  KeyMetricsResponse,
  FunnelMetricsResponse,
  SkillDemandResponse,
  SourceTrackingResponse,
  RecruiterPerformanceResponse,
  RankingMetricsResponse,
  ApiError,
  AnalyticsExportFormat,
  AnalyticsExportRequest,
  AnalyticsExportMetadata,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  KeyMetricsResponse,
  FunnelMetricsResponse,
  SkillDemandResponse,
  SourceTrackingResponse,
  RecruiterPerformanceResponse,
  RankingMetricsResponse,
  AnalyticsExportFormat,
  AnalyticsExportRequest,
  AnalyticsExportMetadata,
};

/**
 * Конфигурация по умолчанию для клиента аналитики
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 30000, // 30 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с аналитикой
 *
 * Предоставляет методы для получения различных метрик и аналитических данных
 * с proper обработкой ошибок и типобезопасностью.
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
      404: 'Данные аналитики не найдены.',
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

  /**
   * Получение ключевых метрик
   *
   * Возвращает ключевые показатели эффективности: time-to-hire, метрики обработки резюме
   * и коэффициенты совпадения навыков.
   *
   * @param startDate - Опциональная начальная дата для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная конечная дата для фильтрации (формат ISO 8601)
   * @returns Ключевые метрики
   * @throws ApiError если получение метрик не удалось
   *
   * @example
   * ```ts
   * // Получение всех метрик
   * const metrics = await analyticsClient.getKeyMetrics();
   *
   * // Получение метрик за период
   * const metrics = await analyticsClient.getKeyMetrics('2024-01-01', '2024-12-31');
   *
   * console.log('Среднее время найма (дни):', metrics.time_to_hire.average_days);
   * console.log('Обработано резюме:', metrics.resumes.total_processed);
   * console.log('Коэффициент совпадения:', metrics.match_rates.overall_match_rate);
   * ```
   */
  async getKeyMetrics(
    startDate?: string,
    endDate?: string
  ): Promise<KeyMetricsResponse> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<KeyMetricsResponse> = await this.client.get(
        '/api/analytics/key-metrics',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение метрик воронки найма
   *
   * Возвращает данные о продвижении кандидатов через этапы воронки
   * с коэффициентами конверсии на каждом этапе.
   *
   * @param startDate - Опциональная начальная дата для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная конечная дата для фильтрации (формат ISO 8601)
   * @returns Метрики воронки найма
   * @throws ApiError если получение метрик не удалось
   *
   * @example
   * ```ts
   * // Получение метрик воронки
   * const funnel = await analyticsClient.getFunnelMetrics();
   *
   * console.log('Этапы:', funnel.stages);
   * console.log('Общий коэффициент найма:', funnel.overall_hire_rate);
   *
   * // Анализ конверсии на каждом этапе
   * funnel.stages.forEach(stage => {
   *   console.log(`${stage.stage_name}: ${stage.count} (${stage.conversion_rate}%)`);
   * });
   *
   * // С фильтрацией по дате
   * const funnel = await analyticsClient.getFunnelMetrics('2024-01-01', '2024-12-31');
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
   * Получение аналитики спроса на навыки
   *
   * Возвращает данные о наиболее востребованных навыках на рынке труда
   * с тенденциями изменения спроса.
   *
   * @param startDate - Опциональная начальная дата для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная конечная дата для фильтрации (формат ISO 8601)
   * @param limit - Опциональное максимальное количество навыков для возврата (1-100, по умолчанию 20)
   * @returns Данные о спросе на навыки
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * // Получение топ-20 востребованных навыков
   * const skills = await analyticsClient.getSkillDemand();
   *
   * console.log('Анализировано вакансий:', skills.total_postings_analyzed);
   *
   * // Топ навыков с тенденциями
   * skills.skills.forEach(skill => {
   *   console.log(`${skill.skill_name}: ${skill.demand_count} (${skill.trend_percentage}%)`);
   * });
   *
   * // Получение топ-30 навыков за период
   * const skills = await analyticsClient.getSkillDemand('2024-01-01', '2024-12-31', 30);
   * ```
   */
  async getSkillDemand(
    startDate?: string,
    endDate?: string,
    limit?: number
  ): Promise<SkillDemandResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (limit !== undefined) params.limit = limit;

      const response: AxiosResponse<SkillDemandResponse> = await this.client.get(
        '/api/analytics/skill-demand',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение аналитики отслеживания источников
   *
   * Возвращает данные о распределении вакансий по источникам
   * с показателями среднего времени заполнения для каждого источника.
   *
   * @param startDate - Опциональная начальная дата для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная конечная дата для фильтрации (формат ISO 8601)
   * @returns Данные об отслеживании источников
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * // Получение данных по источникам
   * const sources = await analyticsClient.getSourceTracking();
   *
   * console.log('Всего вакансий:', sources.total_vacancies);
   *
   * // Анализ эффективности источников
   * sources.sources.forEach(source => {
   *   console.log(`${source.source_name}: ${source.vacancy_count} (${source.percentage}%)`);
   *   console.log(`  Среднее время заполнения: ${source.average_time_to_fill} дней`);
   * });
   *
   * // С фильтрацией по дате
   * const sources = await analyticsClient.getSourceTracking('2024-01-01', '2024-12-31');
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
   * Получение метрик эффективности рекрутеров
   *
   * Возвращает сравнительные данные о производительности рекрутеров
   * включая количество наймов, проведенных собеседований и другие показатели.
   *
   * @param startDate - Опциональная начальная дата для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная конечная дата для фильтрации (формат ISO 8601)
   * @param limit - Опциональное максимальное количество рекрутеров для возврата (1-100, по умолчанию 20)
   * @returns Данные об эффективности рекрутеров
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * // Получение топ-20 рекрутеров
   * const recruiters = await analyticsClient.getRecruiterPerformance();
   *
   * console.log('Период с', recruiters.period_start_date, 'по', recruiters.period_end_date);
   *
   * // Анализ эффективности
   * recruiters.recruiters.forEach(recruiter => {
   *   console.log(`${recruiter.recruiter_name}:`);
   *   console.log(`  Нанято: ${recruiter.hires}`);
   *   console.log(`  Собеседований: ${recruiter.interviews_conducted}`);
   *   console.log(`  Среднее время найма: ${recruiter.average_time_to_hire} дней`);
   *   console.log(`  Принятие офферов: ${recruiter.offer_acceptance_rate}%`);
   * });
   *
   * // Получение топ-10 рекрутеров за период
   * const recruiters = await analyticsClient.getRecruiterPerformance('2024-01-01', '2024-12-31', 10);
   * ```
   */
  async getRecruiterPerformance(
    startDate?: string,
    endDate?: string,
    limit?: number
  ): Promise<RecruiterPerformanceResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (limit !== undefined) params.limit = limit;

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
   * Получение метрик точности ранжирования
   *
   * Возвращает данные о производительности ML-рекомендаций включая
   * коэффициенты конверсии обратной связи, показатели успеха top-N рекомендаций
   * и распределение уверенности ранжирования.
   *
   * @param startDate - Опциональная начальная дата для фильтрации (формат ISO 8601)
   * @param endDate - Опциональная конечная дата для фильтрации (формат ISO 8601)
   * @returns Метрики точности ранжирования
   * @throws ApiError если получение данных не удалось
   *
   * @example
   * ```ts
   * // Получение метрик ранжирования
   * const ranking = await analyticsClient.getRankingAccuracy();
   *
   * console.log('Проанализировано вакансий:', ranking.total_vacancies_analyzed);
   *
   * // Анализ конверсии обратной связи
   * console.log('Коэффициент обратной связи:', ranking.feedback_conversion.feedback_rate);
   * console.log('Положительная обратная связь:', ranking.feedback_conversion.positive_feedback_rate);
   *
   * // Анализ top-N успеха
   * console.log('Top-5 успех:', ranking.top_n_performance.top_5_success_rate);
   * console.log('Наймов из top-5:', ranking.top_n_performance.top_5_hired_count);
   *
   * // С фильтрацией по дате
   * const ranking = await analyticsClient.getRankingAccuracy('2024-01-01', '2024-12-31');
   * ```
   */
  async getRankingAccuracy(
    startDate?: string,
    endDate?: string
  ): Promise<RankingMetricsResponse> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<RankingMetricsResponse> = await this.client.get(
        '/api/analytics/ranking-accuracy',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Экспорт аналитических данных
   *
   * Позволяет экспортировать данные аналитики в формате CSV или JSON
   * для внешнего анализа и отчётности.
   *
   * @param options - Параметры экспорта
   * @param options.format - Формат экспорта ('csv' или 'json', по умолчанию 'csv')
   * @param options.start_date - Начальная дата для фильтрации (формат ISO 8601)
   * @param options.end_date - Конечная дата для фильтрации (формат ISO 8601)
   * @returns Blob с экспортированными данными для скачивания
   * @throws ApiError если экспорт не удался
   *
   * @example
   * ```ts
   * // Экспорт в формате CSV
   * const blob = await analyticsClient.exportAnalytics({ format: 'csv' });
   *
   * // Создание ссылки для скачивания
   * const url = window.URL.createObjectURL(blob);
   * const a = document.createElement('a');
   * a.href = url;
   * a.download = 'analytics_export.csv';
   * a.click();
   * window.URL.revokeObjectURL(url);
   *
   * // Экспорт за период
   * const blob = await analyticsClient.exportAnalytics({
   *   format: 'json',
   *   start_date: '2024-01-01',
   *   end_date: '2024-12-31',
   * });
   * ```
   */
  async exportAnalytics(options: AnalyticsExportRequest = {}): Promise<Blob> {
    try {
      const params: Record<string, string> = {};
      if (options.format) params.format = options.format;
      if (options.start_date) params.start_date = options.start_date;
      if (options.end_date) params.end_date = options.end_date;

      const response: AxiosResponse<Blob> = await this.client.get(
        '/api/analytics/export',
        {
          params,
          responseType: 'blob',
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Экспорт аналитических данных в формате JSON с метаданными
   *
   * Возвращает данные аналитики в формате JSON вместе с метаданными экспорта.
   * Полезно для программной обработки данных.
   *
   * @param options - Параметры экспорта
   * @param options.start_date - Начальная дата для фильтрации (формат ISO 8601)
   * @param options.end_date - Конечная дата для фильтрации (формат ISO 8601)
   * @returns Объект с данными экспорта и метаданными
   * @throws ApiError если экспорт не удался
   *
   * @example
   * ```ts
   * const result = await analyticsClient.exportAnalyticsJson({
   *   start_date: '2024-01-01',
   *   end_date: '2024-12-31',
   * });
   *
   * console.log('Экспортировано записей:', result.metadata.total_records);
   * console.log('Данные:', result.data);
   * ```
   */
  async exportAnalyticsJson(
    options: Omit<AnalyticsExportRequest, 'format'> = {}
  ): Promise<{ data: unknown; metadata: AnalyticsExportMetadata }> {
    try {
      const params: Record<string, string> = { format: 'json' };
      if (options.start_date) params.start_date = options.start_date;
      if (options.end_date) params.end_date = options.end_date;

      const response: AxiosResponse<{ data: unknown; metadata: AnalyticsExportMetadata }> =
        await this.client.get('/api/analytics/export', { params });
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение базового экземпляра Axios
   *
   * Полезно для выполнения кастомных запросов, не покрытых методами клиента.
   *
   * @returns Экземпляр Axios
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }
}

/**
 * Экземпляр клиента аналитики по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с аналитикой.
 */
export const analyticsClient = new AnalyticsClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default AnalyticsClient;
