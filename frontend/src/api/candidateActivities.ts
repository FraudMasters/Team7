/**
 * Candidate Activities API Client
 *
 * Этот модуль предоставляет клиент для получения истории активности кандидата,
 * включая изменения этапов, добавление/изменение заметок, модификацию тегов
 * и другие значимые события кандидата в течение процесса найма.
 *
 * @example
 * ```ts
 * import { candidateActivitiesClient } from '@/api/candidateActivities';
 *
 * // Получение всех активностей для кандидата
 * const activities = await candidateActivitiesClient.listActivities('resume-123');
 *
 * // Фильтрация активностей по типу
 * const stageChanges = await candidateActivitiesClient.filterByType(
 *   'resume-123',
 *   'stage_changed'
 * );
 *
 * // Получение доступных типов активностей
 * const types = await candidateActivitiesClient.getActivityTypes();
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ActivityItem,
  ActivityTimelineResponse,
  ActivityTypesResponse,
  ApiError,
} from '@/types/api';

/**
 * Конфигурация по умолчанию для клиента активностей кандидата
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с активностями кандидата
 *
 * Предоставляет методы для получения истории активности кандидата с proper
 * обработкой ошибок и типобезопасностью.
 */
export class CandidateActivitiesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента активностей кандидата
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
      404: 'Ресурс не найден.',
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
   * Получение списка активностей кандидата с опциональными фильтрами
   *
   * @param resumeId - ID резюме (кандидата)
   * @param activityType - Опциональный фильтр по типу активности
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param limit - Максимальное количество активностей для возврата (по умолчанию: 100)
   * @param offset - Количество активностей для пропуска при пагинации (по умолчанию: 0)
   * @returns Список активностей в хронологическом порядке
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех активностей для кандидата
   * const activities = await candidateActivitiesClient.listActivities('resume-123');
   *
   * // Получение активностей с пагинацией
   * const page1 = await candidateActivitiesClient.listActivities(
   *   'resume-123',
   *   undefined,
   *   undefined,
   *   50,
   *   0
   * );
   *
   * // Фильтрация по вакансии
   * const vacancyActivities = await candidateActivitiesClient.listActivities(
   *   'resume-123',
   *   undefined,
   *   'vacancy-456'
   * );
   * ```
   */
  async listActivities(
    resumeId: string,
    activityType?: string,
    vacancyId?: string,
    limit = 100,
    offset = 0
  ): Promise<ActivityTimelineResponse> {
    try {
      const params: Record<string, string | number> = {
        resume_id: resumeId,
        limit,
        offset,
      };
      if (activityType) params.activity_type = activityType;
      if (vacancyId) params.vacancy_id = vacancyId;

      const response: AxiosResponse<ActivityTimelineResponse> = await this.client.get(
        '/api/candidate-activities/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Фильтрация активностей кандидата по типу
   *
   * Это удобный метод-обертка для listActivities с фильтром по типу активности.
   *
   * @param resumeId - ID резюме (кандидата)
   * @param activityType - Тип активности для фильтрации (например, 'stage_changed', 'note_added')
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param limit - Максимальное количество активностей для возврата (по умолчанию: 100)
   * @param offset - Количество активностей для пропуска при пагинации (по умолчанию: 0)
   * @returns Отфильтрованный список активностей
   * @throws ApiError если фильтрация не удалась
   *
   * @example
   * ```ts
   * // Получение только изменений этапов
   * const stageChanges = await candidateActivitiesClient.filterByType(
   *   'resume-123',
   *   'stage_changed'
   * );
   *
   * // Получение только добавленных заметок
   * const notes = await candidateActivitiesClient.filterByType(
   *   'resume-123',
   *   'note_added'
   * );
   *
   * // Получение добавленных тегов для конкретной вакансии
   * const tags = await candidateActivitiesClient.filterByType(
   *   'resume-123',
   *   'tag_added',
   *   'vacancy-456'
   * );
   * ```
   */
  async filterByType(
    resumeId: string,
    activityType: string,
    vacancyId?: string,
    limit = 100,
    offset = 0
  ): Promise<ActivityTimelineResponse> {
    try {
      const params: Record<string, string | number> = {
        resume_id: resumeId,
        activity_type: activityType,
        limit,
        offset,
      };
      if (vacancyId) params.vacancy_id = vacancyId;

      const response: AxiosResponse<ActivityTimelineResponse> = await this.client.get(
        '/api/candidate-activities/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение доступных типов активностей
   *
   * @returns Список доступных типов активностей, которые можно использовать для фильтрации
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const types = await candidateActivitiesClient.getActivityTypes();
   * console.log(types.activity_types);
   * // [
   * //   'stage_changed',
   * //   'note_added',
   * //   'note_updated',
   * //   'note_deleted',
   * //   'tag_added',
   * //   'tag_removed',
   * //   'ranking_changed',
   * //   'rating_changed',
   * //   'contact_attempt',
   * //   'interview_scheduled',
   * //   'feedback_provided',
   * //   'status_updated'
   * // ]
   * ```
   */
  async getActivityTypes(): Promise<ActivityTypesResponse> {
    try {
      const response: AxiosResponse<ActivityTypesResponse> = await this.client.get(
        '/api/candidate-activities/types'
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
 * Экземпляр клиента активностей кандидата по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с активностями кандидата.
 */
export const candidateActivitiesClient = new CandidateActivitiesClient();

/**
 * Экспорт класса активностей кандидата для создания кастомных экземпляров
 */
export default CandidateActivitiesClient;
