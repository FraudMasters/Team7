/**
 * Matching API Client
 *
 * Этот модуль предоставляет клиент для работы с сервисом мэтчинга (Matching Service).
 * Поддерживает сравнение резюме с вакансиями, управление сравнениями,
 * ранжирование кандидатов и получение результатов мэтчинга.
 *
 * @example
 * ```ts
 * import { matchingClient } from './matching';
 *
 * // Сравнение резюме с вакансией
 * const match = await matchingClient.compareWithVacancy('resume-123', {
 *   id: 'vacancy-456',
 *   title: 'Senior React Developer',
 *   required_skills: ['React', 'TypeScript', 'Node.js'],
 * });
 *
 * // Получение результатов мэтчинга
 * const results = await matchingClient.getMatchResults('result-123');
 *
 * // Создание сравнения нескольких кандидатов
 * const comparison = await matchingClient.createComparison({
 *   vacancy_id: 'vacancy-456',
 *   resume_ids: ['resume-1', 'resume-2', 'resume-3'],
 *   name: 'Frontend Candidates',
 * });
 *
 * // Ранжирование кандидатов
 * const ranking = await matchingClient.rankCandidates({
 *   vacancy_id: 'vacancy-456',
 *   resume_ids: ['resume-1', 'resume-2'],
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  JobVacancy,
  MatchResponse,
  ComparisonCreate,
  ComparisonUpdate,
  ComparisonResponse,
  ComparisonListResponse,
  CompareMultipleRequest,
  ComparisonMatrixData,
  RankingRequest,
  RankingResponse,
  MatchFeedbackRequest,
  MatchFeedbackResponse,
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
  RankingRequest,
  RankingResponse,
};

/**
 * Конфигурация по умолчанию для клиента мэтчинга
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 30000, // 30 секунд для операций мэтчинга
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с сервисом мэтчинга
 *
 * Предоставляет методы для сравнения резюме с вакансиями, управления сравнениями,
 * ранжирования кандидатов и получения результатов с proper обработкой ошибок.
 */
export class MatchingClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента мэтчинга
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
      404: 'Результат мэтчинга не найден.',
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

  /**
   * Сравнение резюме с вакансией
   *
   * Выполняет интеллектуальное сопоставление навыков кандидата с требованиями вакансии,
   * учитывая синонимы и релевантность опыта.
   *
   * @param resumeId - ID резюме для сравнения
   * @param vacancy - Данные вакансии
   * @returns Результаты сравнения с процентом мэтча и детализацией по навыкам
   * @throws ApiError если сравнение не удалось
   *
   * @example
   * ```ts
   * const match = await matchingClient.compareWithVacancy('resume-123', {
   *   id: 'vacancy-456',
   *   title: 'Senior React Developer',
   *   description: 'Looking for experienced React developer...',
   *   required_skills: ['React', 'TypeScript', 'Node.js'],
   * });
   * console.log(match.match_percentage); // 85
   * ```
   */
  async compareWithVacancy(resumeId: string, vacancy: JobVacancy): Promise<MatchResponse> {
    try {
      const response: AxiosResponse<MatchResponse> = await this.client.post(
        '/api/matching/compare',
        {
          resume_id: resumeId,
          vacancy_data: vacancy,
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение результатов мэтчинга по ID
   *
   * @param resultId - ID результата мэтчинга
   * @returns Детальные результаты мэтчинга
   * @throws ApiError если результат не найден
   *
   * @example
   * ```ts
   * const results = await matchingClient.getMatchResults('result-123');
   * console.log(results.match_percentage, results.required_skills_match);
   * ```
   */
  async getMatchResults(resultId: string): Promise<MatchResponse> {
    try {
      const response: AxiosResponse<MatchResponse> = await this.client.get(
        `/api/matching/results/${resultId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Создание нового сравнения кандидатов
   *
   * Создает представление для сравнения нескольких резюме с одной вакансией.
   * Полезно для сравнения кандидатов между собой.
   *
   * @param request - Данные для создания сравнения
   * @returns Созданное сравнение с результатами
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const comparison = await matchingClient.createComparison({
   *   vacancy_id: 'vacancy-456',
   *   resume_ids: ['resume-1', 'resume-2', 'resume-3'],
   *   name: 'Frontend Candidates',
   *   filters: { min_match_percentage: 50 },
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
   * Получение списка сравнений с фильтрами
   *
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param createdBy - Опциональный фильтр по ID создателя
   * @param minMatchPercentage - Опциональный фильтр минимального процента мэтча
   * @param maxMatchPercentage - Опциональный фильтр максимального процента мэтча
   * @param sortBy - Поле сортировки
   * @param order - Порядок сортировки
   * @param limit - Максимальное количество результатов
   * @param offset - Количество результатов для пропуска
   * @returns Список сравнений
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * const comparisons = await matchingClient.listComparisons(
   *   'vacancy-456',
   *   undefined,
   *   50,
   *   undefined,
   *   'match_percentage',
   *   'desc'
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
   * @returns Детали сравнения с результатами
   * @throws ApiError если сравнение не найдено
   *
   * @example
   * ```ts
   * const comparison = await matchingClient.getComparison('comp-123');
   * console.log(comparison.comparison_results);
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
   * @param request - Данные для обновления
   * @returns Обновленное сравнение
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await matchingClient.updateComparison('comp-123', {
   *   name: 'Updated Comparison Name',
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
   * await matchingClient.deleteComparison('comp-123');
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
   * Сравнение нескольких резюме с вакансией
   *
   * Выполняет массовое сравнение резюме с вакансией с ранжированием по проценту мэтча.
   *
   * @param request - Данные для сравнения (vacancy_id, resume_ids)
   * @returns Матрица сравнения с ранжированными результатами
   * @throws ApiError если сравнение не удалось
   *
   * @example
   * ```ts
   * const matrix = await matchingClient.compareMultipleResumes({
   *   vacancy_id: 'vacancy-456',
   *   resume_ids: ['resume-1', 'resume-2', 'resume-3'],
   * });
   * console.log(matrix.comparison_results); // Ranked by match percentage
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

  /**
   * Ранжирование кандидатов по вакансии
   *
   * Выполняет ранжирование списка кандидатов на основе их соответствия вакансии.
   *
   * @param request - Данные для ранжирования
   * @returns Ранжированный список кандидатов
   * @throws ApiError если ранжирование не удалось
   *
   * @example
   * ```ts
   * const ranking = await matchingClient.rankCandidates({
   *   vacancy_id: 'vacancy-456',
   *   resume_ids: ['resume-1', 'resume-2', 'resume-3'],
   * });
   * console.log(ranking.ranked_candidates); // Sorted by rank
   * ```
   */
  async rankCandidates(request: RankingRequest): Promise<RankingResponse> {
    try {
      const response: AxiosResponse<RankingResponse> = await this.client.post(
        '/api/ranking/rank',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Отправка фидбека на результат мэтчинга
   *
   * @param request - Данные фидбека
   * @returns Созданная запись фидбека
   * @throws ApiError если отправка не удалась
   *
   * @example
   * ```ts
   * const feedback = await matchingClient.submitMatchFeedback({
   *   match_id: 'match-123',
   *   skill: 'React',
   *   was_correct: true,
   *   confidence_score: 0.95,
   * });
   * ```
   */
  async submitMatchFeedback(request: MatchFeedbackRequest): Promise<MatchFeedbackResponse> {
    try {
      const response: AxiosResponse<MatchFeedbackResponse> = await this.client.post(
        '/api/matching/feedback',
        request
      );
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
 * Экземпляр клиента мэтчинга по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с мэтчингом.
 */
export const matchingClient = new MatchingClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default MatchingClient;
