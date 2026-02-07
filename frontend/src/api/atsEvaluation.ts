/**
 * ATS Simulation API Client
 *
 * Этот модуль предоставляет клиент для работы с ATS-симуляцией через микросервис.
 * Поддерживает полный цикл управления ATS-оценкой: одиночная оценка, пакетная оценка,
 * получение кэшированных результатов, настройка конфигурации и просмотр истории.
 *
 * @example
 * ```ts
 * import { atsEvaluationClient, AtsEvaluationClient } from '@/api/atsEvaluation';
 *
 * // Оценка резюме для вакансии
 * const result = await atsEvaluationClient.evaluateATS({
 *   resume_id: 'resume-123',
 *   vacancy_id: 'vacancy-456',
 *   use_llm: true,
 * });
 *
 * // Получение кэшированного результата
 * const cached = await atsEvaluationClient.getATSResult('resume-123', 'vacancy-456');
 *
 * // Пакетная оценка
 * const batch = await atsEvaluationClient.batchEvaluateATS({
 *   vacancy_id: 'vacancy-456',
 *   resume_ids: ['resume-1', 'resume-2', 'resume-3'],
 *   use_llm: true,
 * });
 *
 * // Получение конфигурации
 * const config = await atsEvaluationClient.getATSConfig();
 *
 * // Список результатов с фильтрами
 * const results = await atsEvaluationClient.listATSResults(
 *   undefined,
 *   'vacancy-456',
 *   true,
 *   0.6,
 *   50,
 *   0
 * );
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ATSEvaluationRequest,
  ATSEvaluationResponse,
  BatchATSEvaluationRequest,
  BatchATSEvaluationResponse,
  ATSConfigResponse,
  ATSResultListResponse,
  ApiError,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  ATSEvaluationRequest,
  ATSEvaluationResponse,
  BatchATSEvaluationRequest,
  BatchATSEvaluationResponse,
  ATSConfigResponse,
  ATSResultListResponse,
};

/**
 * Конфигурация по умолчанию для клиента ATS-симуляции
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 60000, // 60 секунд (LLM-анализ может занимать больше времени)
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с ATS-симуляцией
 *
 * Предоставляет методы для оценки резюме, пакетной обработки,
 * получения результатов и настройки конфигурации с proper обработкой ошибок
 * и типобезопасностью.
 */
export class AtsEvaluationClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента ATS-симуляции
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
      404: 'Результат не найден.',
      422: 'Ошибка валидации. Проверьте формат данных.',
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
   * Оценка резюме для вакансии через ATS-симуляцию
   *
   * @param request - Параметры оценки (resume_id, vacancy_id, use_llm)
   * @returns Результат ATS-оценки с баллами и рекомендациями
   * @throws ApiError если оценка не удалась
   *
   * @example
   * ```ts
   * const result = await atsEvaluationClient.evaluateATS({
   *   resume_id: 'resume-123',
   *   vacancy_id: 'vacancy-456',
   *   use_llm: true,
   * });
   * console.log(result.passed); // true/false
   * console.log(result.overall_score); // 0-1
   * console.log(result.missing_keywords); // ["Docker", "Kubernetes"]
   * ```
   */
  async evaluateATS(request: ATSEvaluationRequest): Promise<ATSEvaluationResponse> {
    try {
      const response: AxiosResponse<ATSEvaluationResponse> = await this.client.post(
        '/api/ats/evaluate',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение кэшированного результата ATS-оценки для пары резюме-вакансия
   *
   * @param resumeId - ID резюме
   * @param vacancyId - ID вакансии
   * @returns Кэшированный результат ATS-оценки
   * @throws ApiError если результат не найден
   *
   * @example
   * ```ts
   * const result = await atsEvaluationClient.getATSResult('resume-123', 'vacancy-456');
   * console.log(result.passed, result.overall_score);
   * ```
   */
  async getATSResult(resumeId: string, vacancyId: string): Promise<ATSEvaluationResponse> {
    try {
      const response: AxiosResponse<ATSEvaluationResponse> = await this.client.get(
        `/api/ats/results/${resumeId}/${vacancyId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Пакетная оценка нескольких резюме для одной вакансии
   *
   * @param request - Параметры пакетной оценки (vacancy_id, resume_ids, use_llm)
   * @returns Результаты пакетной оценки с итоговой статистикой
   * @throws ApiError если оценка не удалась
   *
   * @example
   * ```ts
   * const result = await atsEvaluationClient.batchEvaluateATS({
   *   vacancy_id: 'vacancy-456',
   *   resume_ids: ['resume-1', 'resume-2', 'resume-3'],
   *   use_llm: true,
   * });
   * console.log(`${result.passed_count}/${result.total_count} passed`);
   * ```
   */
  async batchEvaluateATS(request: BatchATSEvaluationRequest): Promise<BatchATSEvaluationResponse> {
    try {
      const response: AxiosResponse<BatchATSEvaluationResponse> = await this.client.post(
        '/api/ats/batch-evaluate',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение текущей конфигурации ATS-симуляции
   *
   * @returns Конфигурация ATS (provider, model, threshold, weights)
   * @throws ApiError если запрос не удался
   *
   * @example
   * ```ts
   * const config = await atsEvaluationClient.getATSConfig();
   * console.log(config.llm_configured); // true/false
   * console.log(config.provider); // "openai"
   * console.log(config.threshold); // 0.6
   * ```
   */
  async getATSConfig(): Promise<ATSConfigResponse> {
    try {
      const response: AxiosResponse<ATSConfigResponse> = await this.client.get(
        '/api/ats/config'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Список результатов ATS-оценки с опциональными фильтрами
   *
   * @param resumeId - Опциональный фильтр по ID резюме
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param passed - Опциональный фильтр по статусу прохождения
   * @param minScore - Опциональный фильтр по минимальному баллу
   * @param limit - Максимальное количество результатов для возврата
   * @param offset - Количество результатов для пропуска (пагинация)
   * @returns Список результатов ATS-оценки с общим количеством
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех результатов для вакансии
   * const results = await atsEvaluationClient.listATSResults(
   *   undefined,
   *   'vacancy-456'
   * );
   * console.log(`${results.total_count} results found`);
   *
   * // Фильтрация прошедших оценку с высоким баллом
   * const passed = await atsEvaluationClient.listATSResults(
   *   undefined,
   *   'vacancy-456',
   *   true,
   *   0.7,
   *   100,
   *   0
   * );
   * ```
   */
  async listATSResults(
    resumeId?: string,
    vacancyId?: string,
    passed?: boolean,
    minScore?: number,
    limit: number = 50,
    offset: number = 0
  ): Promise<ATSResultListResponse> {
    try {
      const params: Record<string, string | number | boolean> = {};
      if (resumeId) params.resume_id = resumeId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (passed !== undefined) params.passed = passed;
      if (minScore !== undefined) params.min_score = minScore;
      params.limit = limit;
      params.offset = offset;

      const response: AxiosResponse<ATSResultListResponse> = await this.client.get(
        '/api/ats/results',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

/**
 * Синглтон-экземпляр клиента ATS-симуляции для использования во всем приложении
 *
 * @example
 * ```ts
 * import { atsEvaluationClient } from '@/api/atsEvaluation';
 *
 * // Оценка резюме
 * const result = await atsEvaluationClient.evaluateATS({
 *   resume_id: 'resume-123',
 *   vacancy_id: 'vacancy-456',
 *   use_llm: true,
 * });
 * ```
 */
export const atsEvaluationClient = new AtsEvaluationClient();
