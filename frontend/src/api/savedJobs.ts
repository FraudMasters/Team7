/**
 * Saved Jobs API Client
 *
 * Этот модуль предоставляет клиент для работы с сохраненными вакансиями через микросервис Job Application Service.
 * Поддерживает полный цикл управления сохраненными вакансиями: сохранение, просмотр списка, проверка статуса и удаление.
 *
 * @example
 * ```ts
 * import { savedJobsClient, SavedJobsClient } from '@/api/savedJobs';
 *
 * // Сохранение вакансии
 * const saved = await savedJobsClient.saveJob({
 *   vacancy_id: 'vacancy-123',
 *   user_id: 'user-456',
 * });
 *
 * // Получение списка сохраненных вакансий
 * const savedJobs = await savedJobsClient.getSavedJobs('user-456');
 *
 * // Проверка, сохранена ли вакансия
 * const check = await savedJobsClient.checkJobSaved('vacancy-123', 'user-456');
 * console.log(check.is_saved); // true/false
 *
 * // Удаление сохраненной вакансии по ID
 * await savedJobsClient.unsaveJob('saved-job-id');
 *
 * // Удаление сохраненной вакансии по vacancy_id и user_id
 * await savedJobsClient.unsaveJobByVacancy('vacancy-123', 'user-456');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ApiError,
  SaveJobRequest,
  SavedJobResponse,
  SavedJobsListResponse,
  CheckJobSavedResponse,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  SaveJobRequest,
  SavedJobResponse,
  SavedJobsListResponse,
  CheckJobSavedResponse,
};

/**
 * Конфигурация по умолчанию для клиента сохраненных вакансий
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с сохраненными вакансиями
 *
 * Предоставляет методы для CRUD-операций с сохраненными вакансиями с proper
 * обработкой ошибок и типобезопасностью.
 */
export class SavedJobsClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента сохраненных вакансий
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
      404: 'Сохраненная вакансия не найдена.',
      409: 'Вакансия уже сохранена.',
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
   * Сохранение вакансии
   *
   * @param data - Данные для сохранения вакансии
   * @returns Сохраненная вакансия с присвоенным ID
   * @throws ApiError если сохранение не удалось
   *
   * @example
   * ```ts
   * const saved = await savedJobsClient.saveJob({
   *   vacancy_id: 'vacancy-123',
   *   user_id: 'user-456',
   * });
   * console.log(`Вакансия сохранена с ID: ${saved.id}`);
   * ```
   */
  async saveJob(data: SaveJobRequest): Promise<SavedJobResponse> {
    try {
      const response: AxiosResponse<SavedJobResponse> = await this.client.post(
        '/api/saved-jobs/save',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка сохраненных вакансий пользователя
   *
   * @param userId - ID пользователя
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимальное количество записей для возврата
   * @returns Список сохраненных вакансий с общим количеством
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение первых 50 сохраненных вакансий
   * const savedJobs = await savedJobsClient.getSavedJobs('user-456', 0, 50);
   *
   * // Пагинация
   * const page2 = await savedJobsClient.getSavedJobs('user-456', 50, 50);
   * ```
   */
  async getSavedJobs(
    userId: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<SavedJobsListResponse> {
    try {
      const response: AxiosResponse<SavedJobsListResponse> = await this.client.get(
        '/api/saved-jobs/',
        {
          params: {
            user_id: userId,
            skip,
            limit,
          },
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Проверка, сохранена ли вакансия пользователем
   *
   * @param vacancyId - ID вакансии
   * @param userId - ID пользователя
   * @returns Результат проверки с флагом is_saved и ID сохраненной вакансии
   * @throws ApiError если проверка не удалась
   *
   * @example
   * ```ts
   * const check = await savedJobsClient.checkJobSaved('vacancy-123', 'user-456');
   * if (check.is_saved) {
   *   console.log(`Вакансия сохранена с ID: ${check.saved_job_id}`);
   * } else {
   *   console.log('Вакансия не сохранена');
   * }
   * ```
   */
  async checkJobSaved(
    vacancyId: string,
    userId: string
  ): Promise<CheckJobSavedResponse> {
    try {
      const response: AxiosResponse<CheckJobSavedResponse> = await this.client.get(
        '/api/saved-jobs/check',
        {
          params: {
            vacancy_id: vacancyId,
            user_id: userId,
          },
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление сохраненной вакансии по ID
   *
   * @param savedJobId - ID сохраненной вакансии
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await savedJobsClient.unsaveJob('saved-job-id-123');
   * console.log('Вакансия удалена из сохраненных');
   * ```
   */
  async unsaveJob(savedJobId: string): Promise<void> {
    try {
      await this.client.delete(`/api/saved-jobs/${savedJobId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление сохраненной вакансии по vacancy_id и user_id
   *
   * Это удобный метод для удаления сохраненной вакансии без знания её ID.
   *
   * @param vacancyId - ID вакансии
   * @param userId - ID пользователя
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await savedJobsClient.unsaveJobByVacancy('vacancy-123', 'user-456');
   * console.log('Вакансия удалена из сохраненных');
   * ```
   */
  async unsaveJobByVacancy(vacancyId: string, userId: string): Promise<void> {
    try {
      await this.client.delete('/api/saved-jobs/unsave', {
        params: {
          vacancy_id: vacancyId,
          user_id: userId,
        },
      });
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
 * Экземпляр клиента сохраненных вакансий по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с сохраненными вакансиями.
 */
export const savedJobsClient = new SavedJobsClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default SavedJobsClient;
