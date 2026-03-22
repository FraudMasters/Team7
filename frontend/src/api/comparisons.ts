/**
 * Comparisons API Client
 *
 * Этот модуль предоставляет клиент для работы со сравнениями резюме.
 * Поддерживает полный цикл управления сравнениями: создание, просмотр списка,
 * просмотр деталей, обновление, удаление и множественное сравнение резюме с вакансией.
 *
 * @example
 * ```ts
 * import { comparisonsClient, ComparisonsClient } from '@/api/comparisons';
 *
 * // Создание нового сравнения
 * const comparison = await comparisonsClient.createComparison({
 *   vacancy_id: 'vacancy-123',
 *   resume_ids: ['resume-1', 'resume-2', 'resume-3'],
 *   name: 'Top Candidates for Senior Developer',
 * });
 *
 * // Получение списка сравнений с фильтрацией
 * const list = await comparisonsClient.listComparisons('vacancy-123');
 *
 * // Сравнение множественных резюме
 * const matrix = await comparisonsClient.compareMultipleResumes({
 *   vacancy_id: 'vacancy-123',
 *   resume_ids: ['resume-1', 'resume-2'],
 * });
 *
 * // Обновление сравнения
 * const updated = await comparisonsClient.updateComparison('comparison-123', {
 *   name: 'Updated Name',
 * });
 *
 * // Удаление сравнения
 * await comparisonsClient.deleteComparison('comparison-123');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ComparisonCreate,
  ComparisonUpdate,
  ComparisonResponse,
  ComparisonListResponse,
  CompareMultipleRequest,
  ComparisonMatrixData,
  ApiError,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  ComparisonCreate,
  ComparisonUpdate,
  ComparisonResponse,
  ComparisonListResponse,
  CompareMultipleRequest,
  ComparisonMatrixData,
};

/**
 * Конфигурация по умолчанию для клиента сравнений
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы со сравнениями резюме
 *
 * Предоставляет методы для создания, просмотра, обновления и удаления сравнений
 * с proper обработкой ошибок и типобезопасностью.
 */
export class ComparisonsClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента сравнений
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
      404: 'Сравнение не найдено.',
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
   * Создание нового сравнения резюме
   *
   * @param request - Запрос на создание сравнения
   * @returns Созданное сравнение
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const comparison = await comparisonsClient.createComparison({
   *   vacancy_id: 'vacancy-123',
   *   resume_ids: ['resume-1', 'resume-2', 'resume-3'],
   *   name: 'Top Candidates for Senior Developer',
   *   filters: { min_experience: 5 },
   * });
   * ```
   */
  async createComparison(request: ComparisonCreate): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.post(
        '/api/comparisons/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка сравнений с опциональными фильтрами и сортировкой
   *
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param createdBy - Опциональный фильтр по ID создателя
   * @param minMatchPercentage - Опциональный минимальный процент совпадения (0-100)
   * @param maxMatchPercentage - Опциональный максимальный процент совпадения (0-100)
   * @param sortBy - Поле для сортировки: created_at, match_percentage, name, updated_at
   * @param order - Порядок сортировки: asc или desc
   * @param limit - Максимальное количество результатов
   * @param offset - Смещение для пагинации
   * @returns Список сравнений с метаданными
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех сравнений для вакансии
   * const list = await comparisonsClient.listComparisons('vacancy-123');
   *
   * // Фильтрация по проценту совпадения с сортировкой
   * const filtered = await comparisonsClient.listComparisons(
   *   'vacancy-123',
   *   undefined,
   *   80,
   *   100,
   *   'match_percentage',
   *   'desc'
   * );
   *
   * // Пагинация
   * const paginated = await comparisonsClient.listComparisons(
   *   undefined,
   *   undefined,
   *   undefined,
   *   undefined,
   *   undefined,
   *   undefined,
   *   10,
   *   20
   * );
   * ```
   */
  async listComparisons(
    vacancyId?: string,
    createdBy?: string,
    minMatchPercentage?: number,
    maxMatchPercentage?: number,
    sortBy?: string,
    order?: string,
    limit?: number,
    offset?: number
  ): Promise<ComparisonListResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (vacancyId) params.vacancy_id = vacancyId;
      if (createdBy) params.created_by = createdBy;
      if (minMatchPercentage !== undefined) params.min_match_percentage = minMatchPercentage;
      if (maxMatchPercentage !== undefined) params.max_match_percentage = maxMatchPercentage;
      if (sortBy) params.sort_by = sortBy;
      if (order) params.order = order;
      if (limit !== undefined) params.limit = limit;
      if (offset !== undefined) params.offset = offset;

      const response: AxiosResponse<ComparisonListResponse> = await this.client.get(
        '/api/comparisons/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение сравнения по ID
   *
   * @param id - ID сравнения
   * @returns Детали сравнения
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const comparison = await comparisonsClient.getComparison('comparison-123');
   * console.log(`Сравнение для вакансии: ${comparison.vacancy_id}`);
   * console.log(`Количество резюме: ${comparison.resume_ids.length}`);
   * ```
   */
  async getComparison(id: string): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.get(
        `/api/comparisons/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление сравнения
   *
   * @param id - ID сравнения
   * @param request - Запрос на обновление с полями для изменения
   * @returns Обновленное сравнение
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await comparisonsClient.updateComparison('comparison-123', {
   *   name: 'Updated Comparison Name',
   *   filters: { min_experience: 7 },
   *   shared_with: ['user-1', 'user-2'],
   * });
   * ```
   */
  async updateComparison(
    id: string,
    request: ComparisonUpdate
  ): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.put(
        `/api/comparisons/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление сравнения
   *
   * @param id - ID сравнения
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await comparisonsClient.deleteComparison('comparison-123');
   * ```
   */
  async deleteComparison(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/comparisons/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Сравнение множественных резюме с вакансией
   *
   * Этот метод выполняет интеллектуальное сопоставление навыков каждого резюме
   * с требованиями вакансии, обрабатывая синонимы (например, PostgreSQL ≈ SQL)
   * и предоставляя агрегированные результаты с ранжированием по проценту совпадения.
   *
   * @param request - Запрос на сравнение с vacancy_id и resume_ids
   * @returns Данные матрицы сравнения с ранжированными результатами
   * @throws ApiError если сравнение не удалось
   *
   * @example
   * ```ts
   * const matrix = await comparisonsClient.compareMultipleResumes({
   *   vacancy_id: 'vacancy-123',
   *   resume_ids: ['resume-1', 'resume-2', 'resume-3'],
   * });
   *
   * console.log(`Вакансия: ${matrix.vacancy_title}`);
   * console.log(`Обработано резюме: ${matrix.total_resumes}`);
   * console.log(`Время обработки: ${matrix.processing_time_ms}ms`);
   *
   * matrix.comparison_results.forEach((result) => {
   *   console.log(`Ранг ${result.rank}: ${result.resume_id} - ${result.match_percentage}%`);
   * });
   * ```
   */
  async compareMultipleResumes(request: CompareMultipleRequest): Promise<ComparisonMatrixData> {
    try {
      const response: AxiosResponse<ComparisonMatrixData> = await this.client.post(
        '/api/comparisons/compare-multiple',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

/**
 * Синглтон экземпляр клиента сравнений для удобного использования
 *
 * @example
 * ```ts
 * import { comparisonsClient } from '@/api/comparisons';
 *
 * const comparison = await comparisonsClient.createComparison({
 *   vacancy_id: 'vacancy-123',
 *   resume_ids: ['resume-1', 'resume-2'],
 * });
 * ```
 */
export const comparisonsClient = new ComparisonsClient();
