/**
 * Fairness Monitoring API Client
 *
 * Этот модуль предоставляет удобный интерфейс для мониторинга справедливости AI моделей,
 * включая получение метрик справедливости, отчетов о смещении и оповещений о дискриминации.
 *
 * @example
 * ```ts
 * import { fairness } from '@/api/fairness';
 *
 * // Получение сводки справедливости
 * const summary = await fairness.getSummary();
 *
 * // Получение метрик справедливости
 * const metrics = await fairness.getMetrics({
 *   model_name: 'ranking',
 *   protected_attribute: 'gender',
 * });
 *
 * // Получение отчетов о смещении
 * const reports = await fairness.getReports({
 *   severity_level: 'high',
 * });
 *
 * // Генерация нового отчета о смещении
 * const report = await fairness.generateReport({
 *   model_name: 'ranking',
 *   report_type: 'system-wide',
 * });
 *
 * // Подтверждение оповещения
 * await fairness.acknowledgeAlert('alert-123');
 * ```
 */

import axios, { AxiosInstance } from 'axios';
import type {
  FairnessMetric,
  FairnessMetricsListResponse,
  BiasReport,
  BiasReportListResponse,
  FairnessAlert,
  FairnessAlertListResponse,
  FairnessSummary,
  GenerateBiasReportRequest,
  AcknowledgeAlertResponse,
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
 * Класс клиента мониторинга справедливости
 *
 * Предоставляет методы для метрик справедливости, отчетов о смещении и оповещений.
 */
export class FairnessClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента справедливости
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
   * Получение метрик справедливости для AI моделей
   *
   * @param options - Опциональные фильтры для метрик
   * @returns Список метрик справедливости
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const metrics = await fairness.getMetrics({
   *   model_name: 'ranking',
   *   protected_attribute: 'gender',
   *   metric_type: 'disparate_impact',
   *   is_acceptable: false,
   *   limit: 50,
   * });
   * ```
   */
  async getMetrics(options?: {
    model_name?: string;
    model_version?: string;
    protected_attribute?: string;
    metric_type?: string;
    is_acceptable?: boolean;
    limit?: number;
  }): Promise<FairnessMetricsListResponse> {
    try {
      const params = new URLSearchParams();

      if (options?.model_name) params.append('model_name', options.model_name);
      if (options?.model_version) params.append('model_version', options.model_version);
      if (options?.protected_attribute) params.append('protected_attribute', options.protected_attribute);
      if (options?.metric_type) params.append('metric_type', options.metric_type);
      if (options?.is_acceptable !== undefined) params.append('is_acceptable', String(options.is_acceptable));
      if (options?.limit) params.append('limit', String(options.limit));

      const queryString = params.toString();
      const url = `/api/fairness/metrics${queryString ? `?${queryString}` : ''}`;

      const response = await this.client.get<FairnessMetricsListResponse>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Получение отчетов об анализе смещения
   *
   * @param options - Опциональные фильтры для отчетов
   * @returns Список отчетов о смещении
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const reports = await fairness.getReports({
   *   model_name: 'ranking',
   *   severity_level: 'high',
   *   bias_detected: true,
   *   limit: 20,
   * });
   * ```
   */
  async getReports(options?: {
    model_name?: string;
    model_version?: string;
    report_type?: string;
    severity_level?: string;
    bias_detected?: boolean;
    limit?: number;
  }): Promise<BiasReportListResponse> {
    try {
      const params = new URLSearchParams();

      if (options?.model_name) params.append('model_name', options.model_name);
      if (options?.model_version) params.append('model_version', options.model_version);
      if (options?.report_type) params.append('report_type', options.report_type);
      if (options?.severity_level) params.append('severity_level', options.severity_level);
      if (options?.bias_detected !== undefined) params.append('bias_detected', String(options.bias_detected));
      if (options?.limit) params.append('limit', String(options.limit));

      const queryString = params.toString();
      const url = `/api/fairness/reports${queryString ? `?${queryString}` : ''}`;

      const response = await this.client.get<BiasReportListResponse>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Получение оповещений о справедливости
   *
   * @param options - Опциональные фильтры для оповещений
   * @returns Список оповещений о справедливости
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const alerts = await fairness.getAlerts({
   *   model_name: 'ranking',
   *   severity: 'high',
   *   acknowledged: false,
   *   days: 7,
   *   limit: 50,
   * });
   * ```
   */
  async getAlerts(options?: {
    model_name?: string;
    alert_type?: string;
    severity?: string;
    acknowledged?: boolean;
    days?: number;
    limit?: number;
  }): Promise<FairnessAlertListResponse> {
    try {
      const params = new URLSearchParams();

      if (options?.model_name) params.append('model_name', options.model_name);
      if (options?.alert_type) params.append('alert_type', options.alert_type);
      if (options?.severity) params.append('severity', options.severity);
      if (options?.acknowledged !== undefined) params.append('acknowledged', String(options.acknowledged));
      if (options?.days) params.append('days', String(options.days));
      if (options?.limit) params.append('limit', String(options.limit));

      const queryString = params.toString();
      const url = `/api/fairness/alerts${queryString ? `?${queryString}` : ''}`;

      const response = await this.client.get<FairnessAlertListResponse>(url);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Получение сводки справедливости по всем моделям
   *
   * @returns Сводка справедливости
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const summary = await fairness.getSummary();
   * console.log(summary.overall_fairness_score);
   * console.log(summary.models_with_issues);
   * ```
   */
  async getSummary(): Promise<FairnessSummary> {
    try {
      const response = await this.client.get<FairnessSummary>('/api/fairness/summary');
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Генерация нового отчета об анализе смещения
   *
   * @param request - Запрос на генерацию отчета
   * @returns Сгенерированный отчет о смещении
   * @throws ApiError если генерация не удалась
   *
   * @example
   * ```ts
   * const report = await fairness.generateReport({
   *   model_name: 'ranking',
   *   model_version: 'v1.0.0',
   *   report_type: 'system-wide',
   * });
   * ```
   */
  async generateReport(request: GenerateBiasReportRequest): Promise<BiasReport> {
    try {
      const params = new URLSearchParams();
      params.append('model_name', request.model_name);
      if (request.model_version) params.append('model_version', request.model_version);
      if (request.report_type) params.append('report_type', request.report_type);

      const response = await this.client.post<BiasReport>(
        `/api/fairness/reports/generate?${params.toString()}`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Подтверждение оповещения о справедливости
   *
   * @param alertId - ID оповещения для подтверждения
   * @returns Ответ о подтверждении
   * @throws ApiError если подтверждение не удалось
   *
   * @example
   * ```ts
   * const result = await fairness.acknowledgeAlert('alert-123');
   * console.log(result.acknowledged); // true
   * ```
   */
  async acknowledgeAlert(alertId: string): Promise<AcknowledgeAlertResponse> {
    try {
      const response = await this.client.post<AcknowledgeAlertResponse>(
        `/api/fairness/alerts/${alertId}/acknowledge`
      );
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Получение конкретного отчета о смещении по ID
   *
   * @param reportId - ID отчета
   * @returns Детали отчета о смещении
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const report = await fairness.getReport('report-123');
   * ```
   */
  async getReport(reportId: string): Promise<BiasReport> {
    try {
      const response = await this.client.get<BiasReport>(`/api/fairness/reports/${reportId}`);
      return response.data;
    } catch (error) {
      throw transformError(error);
    }
  }

  /**
   * Получение метрик справедливости для конкретной модели
   *
   * @param modelName - Название модели
   * @param options - Опциональные фильтры
   * @returns Метрики справедливости для модели
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const metrics = await fairness.getModelMetrics('ranking', {
   *   protected_attribute: 'gender',
   * });
   * ```
   */
  async getModelMetrics(
    modelName: string,
    options?: {
      model_version?: string;
      protected_attribute?: string;
      metric_type?: string;
      limit?: number;
    }
  ): Promise<FairnessMetricsListResponse> {
    return this.getMetrics({
      model_name: modelName,
      ...options,
    });
  }

  /**
   * Получение оповещений для конкретной модели
   *
   * @param modelName - Название модели
   * @param options - Опциональные фильтры
   * @returns Оповещения для модели
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const alerts = await fairness.getModelAlerts('ranking', {
   *   severity: 'high',
   *   acknowledged: false,
   * });
   * ```
   */
  async getModelAlerts(
    modelName: string,
    options?: {
      alert_type?: string;
      severity?: string;
      acknowledged?: boolean;
      days?: number;
      limit?: number;
    }
  ): Promise<FairnessAlertListResponse> {
    return this.getAlerts({
      model_name: modelName,
      ...options,
    });
  }

  /**
   * Получение критических неподтвержденных оповещений
   *
   * Удобный метод для получения высокоприоритетных оповещений, требующих внимания.
   *
   * @returns Критические оповещения
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const criticalAlerts = await fairness.getCriticalAlerts();
   * ```
   */
  async getCriticalAlerts(): Promise<FairnessAlertListResponse> {
    return this.getAlerts({
      severity: 'critical',
      acknowledged: false,
      days: 7,
      limit: 100,
    });
  }
}

/**
 * Экземпляр клиента справедливости по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех вызовов API справедливости.
 */
export const fairness = new FairnessClient();

/**
 * Экспорт класса клиента справедливости для создания кастомных экземпляров
 */
export default FairnessClient;
