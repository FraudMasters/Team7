/**
 * Feedback API Client
 *
 * Этот модуль предоставляет клиент для работы с отзывами и обратной связью
 * через микросервис Feedback Service. Поддерживает полный цикл управления отзывами:
 * создание, просмотр списка, просмотр деталей, обновление и удаление.
 *
 * @example
 * ```ts
 * import { feedbackClient, FeedbackClient } from '@/api/feedback';
 *
 * // Создание новых отзывов
 * const result = await feedbackClient.createFeedback({
 *   feedback: [
 *     {
 *       resume_id: 'abc123',
 *       vacancy_id: 'vac456',
 *       skill: 'React',
 *       was_correct: true,
 *       confidence_score: 0.95,
 *       feedback_source: 'frontend',
 *     },
 *   ],
 * });
 *
 * // Получение списка отзывов с фильтрами
 * const list = await feedbackClient.listFeedback('abc123', 'vac456', 'React');
 *
 * // Получение отзыва по ID
 * const feedback = await feedbackClient.getFeedback('feedback-123');
 *
 * // Обновление отзыва
 * const updated = await feedbackClient.updateFeedback('feedback-123', {
 *   was_correct: false,
 *   recruiter_correction: 'Actually meant React.js',
 * });
 *
 * // Удаление отзыва
 * await feedbackClient.deleteFeedback('feedback-123');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  FeedbackCreate,
  FeedbackUpdate,
  FeedbackResponse,
  FeedbackListResponse,
  ApiError,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  FeedbackCreate,
  FeedbackUpdate,
  FeedbackResponse,
  FeedbackListResponse,
};

/**
 * Конфигурация по умолчанию для клиента отзывов
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с отзывами
 *
 * Предоставляет методы для создания, просмотра, обновления и удаления отзывов
 * с proper обработкой ошибок и типобезопасностью.
 */
export class FeedbackClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента отзывов
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
      404: 'Отзыв не найден.',
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
   * Создание новых отзывов
   *
   * @param request - Запрос на создание со списком отзывов
   * @returns Созданные отзывы
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const result = await feedbackClient.createFeedback({
   *   feedback: [
   *     {
   *       resume_id: 'abc123',
   *       vacancy_id: 'vac456',
   *       skill: 'React',
   *       was_correct: true,
   *       confidence_score: 0.95,
   *       feedback_source: 'frontend',
   *     },
   *     {
   *       resume_id: 'abc123',
   *       vacancy_id: 'vac456',
   *       skill: 'TypeScript',
   *       was_correct: false,
   *       actual_skill: 'JavaScript',
   *       feedback_source: 'frontend',
   *     },
   *   ],
   * });
   * ```
   */
  async createFeedback(request: FeedbackCreate): Promise<FeedbackListResponse> {
    try {
      const response: AxiosResponse<FeedbackListResponse> = await this.client.post(
        '/api/feedback/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка отзывов с опциональными фильтрами
   *
   * @param resumeId - Опциональный фильтр по ID резюме
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param skill - Опциональный фильтр по навыку
   * @param wasCorrect - Опциональный фильтр по корректности
   * @param processed - Опциональный фильтр по статусу обработки
   * @param feedbackSource - Опциональный фильтр по источнику отзыва
   * @returns Список отзывов
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех отзывов
   * const all = await feedbackClient.listFeedback();
   *
   * // Фильтрация по резюме и вакансии
   * const filtered = await feedbackClient.listFeedback('abc123', 'vac456');
   *
   * // Фильтрация по навыку и корректности
   * const skills = await feedbackClient.listFeedback(undefined, undefined, 'React', true);
   * ```
   */
  async listFeedback(
    resumeId?: string,
    vacancyId?: string,
    skill?: string,
    wasCorrect?: boolean,
    processed?: boolean,
    feedbackSource?: string
  ): Promise<FeedbackListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (resumeId) params.resume_id = resumeId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (skill) params.skill = skill;
      if (wasCorrect !== undefined) params.was_correct = wasCorrect;
      if (processed !== undefined) params.processed = processed;
      if (feedbackSource) params.feedback_source = feedbackSource;

      const response: AxiosResponse<FeedbackListResponse> = await this.client.get(
        '/api/feedback/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение отзыва по ID
   *
   * @param id - ID отзыва
   * @returns Данные отзыва
   * @throws ApiError если отзыв не найден
   *
   * @example
   * ```ts
   * const feedback = await feedbackClient.getFeedback('feedback-123');
   * console.log(feedback.skill, feedback.was_correct);
   * ```
   */
  async getFeedback(id: string): Promise<FeedbackResponse> {
    try {
      const response: AxiosResponse<FeedbackResponse> = await this.client.get(
        `/api/feedback/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление отзыва
   *
   * @param id - ID отзыва
   * @param request - Запрос на обновление
   * @returns Обновленный отзыв
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await feedbackClient.updateFeedback('feedback-123', {
   *   was_correct: false,
   *   recruiter_correction: 'Actually meant React.js',
   *   processed: true,
   * });
   * ```
   */
  async updateFeedback(
    id: string,
    request: FeedbackUpdate
  ): Promise<FeedbackResponse> {
    try {
      const response: AxiosResponse<FeedbackResponse> = await this.client.put(
        `/api/feedback/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление отзыва
   *
   * @param id - ID отзыва
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await feedbackClient.deleteFeedback('feedback-123');
   * ```
   */
  async deleteFeedback(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/feedback/${id}`);
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
 * Экземпляр клиента отзывов по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с отзывами.
 */
export const feedbackClient = new FeedbackClient();

/**
 * Экспорт класса отзывов для создания кастомных экземпляров
 */
export default FeedbackClient;
