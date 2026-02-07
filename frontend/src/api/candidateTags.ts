/**
 * Candidate Tags API Client
 *
 * Этот модуль предоставляет клиент для управления тегами кандидатов организации,
 * включая создание, чтение, обновление и удаление конфигураций тегов, а также
 * назначение и удаление тегов у кандидатов (резюме). Теги обеспечивают гибкую
 * категоризацию и приоритизацию (например, 'Высокий приоритет', 'Удаленно', 'Рекомендация').
 *
 * @example
 * ```ts
 * import { candidateTagsClient } from '@/api/candidateTags';
 *
 * // Получение всех тегов для организации
 * const tags = await candidateTagsClient.listTags('org-123');
 *
 * // Создание нового тега
 * const newTag = await candidateTagsClient.createTag({
 *   organization_id: 'org-123',
 *   tag_name: 'Высокий приоритет',
 *   tag_order: 1,
 *   is_active: true,
 *   color: '#EF4444',
 *   description: 'Для срочных или высокоприоритетных кандидатов'
 * });
 *
 * // Назначение тега резюме
 * await candidateTagsClient.assignTagToResume('resume-id', {
 *   tag_id: 'tag-id',
 *   recruiter_id: 'recruiter-id'
 * });
 *
 * // Обновление тега
 * const updated = await candidateTagsClient.updateTag('tag-id', {
 *   tag_name: 'Обновленное название тега',
 *   is_active: false
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  CandidateTagCreate,
  CandidateTagUpdate,
  CandidateTagResponse,
  CandidateTagListResponse,
  CandidateTagsResponse,
  AssignTagRequest,
  ApiError,
} from '@/types/api';

/**
 * Конфигурация по умолчанию для клиента тегов кандидата
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с тегами кандидата
 *
 * Предоставляет методы для управления конфигурациями тегов кандидата с proper
 * обработкой ошибок и типобезопасностью.
 */
export class CandidateTagsClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента тегов кандидата
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
      409: 'Тег с таким названием уже существует.',
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
   * Создание тега кандидата для организации
   *
   * @param request - Запрос на создание с деталями тега
   * @returns Созданный тег кандидата
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const tag = await candidateTagsClient.createTag({
   *   organization_id: 'org-123',
   *   tag_name: 'Высокий приоритет',
   *   tag_order: 1,
   *   is_active: true,
   *   color: '#EF4444',
   *   description: 'Для срочных или высокоприоритетных кандидатов'
   * });
   * ```
   */
  async createTag(request: CandidateTagCreate): Promise<CandidateTagResponse> {
    try {
      const response: AxiosResponse<CandidateTagResponse> = await this.client.post(
        '/api/candidate-tags/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка тегов кандидата с опциональными фильтрами
   *
   * @param organizationId - Опциональный фильтр по ID организации
   * @param isActive - Опциональный фильтр по активному статусу
   * @param isDefault - Опциональный фильтр по статусу по умолчанию
   * @returns Список тегов кандидата
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех тегов для организации
   * const tags = await candidateTagsClient.listTags('org-123');
   *
   * // Получение только активных тегов
   * const activeTags = await candidateTagsClient.listTags('org-123', true);
   * ```
   */
  async listTags(
    organizationId?: string,
    isActive?: boolean,
    isDefault?: boolean
  ): Promise<CandidateTagListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (isActive !== undefined) params.is_active = isActive;
      if (isDefault !== undefined) params.is_default = isDefault;

      const response: AxiosResponse<CandidateTagListResponse> = await this.client.get(
        '/api/candidate-tags/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение конкретного тега кандидата по ID
   *
   * @param tagId - ID тега кандидата
   * @returns Детали тега кандидата
   * @throws ApiError если тег не найден
   *
   * @example
   * ```ts
   * const tag = await candidateTagsClient.getTag('tag-uuid');
   * ```
   */
  async getTag(tagId: string): Promise<CandidateTagResponse> {
    try {
      const response: AxiosResponse<CandidateTagResponse> = await this.client.get(
        `/api/candidate-tags/${tagId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение всех тегов, назначенных конкретному резюме
   *
   * @param resumeId - ID резюме
   * @returns Теги, назначенные этому резюме
   * @throws ApiError если резюме не найдено
   *
   * @example
   * ```ts
   * const tags = await candidateTagsClient.getResumeTags('resume-uuid');
   * ```
   */
  async getResumeTags(resumeId: string): Promise<CandidateTagsResponse> {
    try {
      const response: AxiosResponse<CandidateTagsResponse> = await this.client.get(
        `/api/candidate-tags/resume/${resumeId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление тега кандидата
   *
   * @param tagId - ID тега кандидата
   * @param request - Запрос на обновление с полями для изменения
   * @returns Обновленный тег кандидата
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await candidateTagsClient.updateTag('tag-uuid', {
   *   tag_name: 'Обновленное название тега',
   *   is_active: false
   * });
   * ```
   */
  async updateTag(
    tagId: string,
    request: CandidateTagUpdate
  ): Promise<CandidateTagResponse> {
    try {
      const response: AxiosResponse<CandidateTagResponse> = await this.client.put(
        `/api/candidate-tags/${tagId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление тега кандидата
   *
   * @param tagId - ID тега кандидата
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await candidateTagsClient.deleteTag('tag-uuid');
   * ```
   */
  async deleteTag(tagId: string): Promise<void> {
    try {
      await this.client.delete(`/api/candidate-tags/${tagId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Назначение тега кандидату (резюме)
   *
   * @param resumeId - ID резюме
   * @param request - Запрос на назначение тега
   * @returns Ответ об успехе с ID активности
   * @throws ApiError если назначение не удалось
   *
   * @example
   * ```ts
   * const result = await candidateTagsClient.assignTagToResume('resume-uuid', {
   *   tag_id: 'tag-uuid',
   *   recruiter_id: 'recruiter-uuid'
   * });
   * ```
   */
  async assignTagToResume(
    resumeId: string,
    request: AssignTagRequest
  ): Promise<{ message: string; resume_id: string; tag_id: string; activity_id: string }> {
    try {
      const response = await this.client.post(
        `/api/candidate-tags/resume/${resumeId}/assign`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление тега у кандидата (резюме)
   *
   * @param resumeId - ID резюме
   * @param tagId - ID тега для удаления
   * @param recruiterId - Опциональный ID рекрутера, который удаляет тег
   * @returns Ответ об успехе с ID активности
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * const result = await candidateTagsClient.removeTagFromResume(
   *   'resume-uuid',
   *   'tag-uuid',
   *   'recruiter-uuid'
   * );
   * ```
   */
  async removeTagFromResume(
    resumeId: string,
    tagId: string,
    recruiterId?: string
  ): Promise<{ message: string; resume_id: string; tag_id: string; activity_id: string }> {
    try {
      const params: Record<string, string> = {};
      if (recruiterId) params.recruiter_id = recruiterId;

      const response = await this.client.delete(
        `/api/candidate-tags/resume/${resumeId}/tags/${tagId}`,
        { params }
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
 * Экземпляр клиента тегов кандидата по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с тегами кандидата.
 */
export const candidateTagsClient = new CandidateTagsClient();

/**
 * Экспорт класса тегов кандидата для создания кастомных экземпляров
 */
export default CandidateTagsClient;
