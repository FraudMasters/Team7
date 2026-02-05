/**
 * Candidate Notes API Client
 *
 * Этот модуль предоставляет клиент для управления заметками и комментариями кандидата,
 * включая создание, чтение, обновление и удаление совместных заметок.
 *
 * @example
 * ```ts
 * import { candidateNotesClient } from '@/api/candidateNotes';
 *
 * // Получение всех заметок для кандидата
 * const notes = await candidateNotesClient.listNotes('resume-123');
 *
 * // Создание новой заметки
 * const newNote = await candidateNotesClient.createNote({
 *   resume_id: 'resume-123',
 *   content: 'Отличный кандидат, сильные технические навыки',
 *   recruiter_id: 'recruiter-123',
 *   is_private: false
 * });
 *
 * // Обновление заметки
 * const updated = await candidateNotesClient.updateNote('note-id', {
 *   content: 'Обновленное содержание заметки',
 *   is_private: true
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  CandidateNoteCreate,
  CandidateNoteUpdate,
  CandidateNoteResponse,
  CandidateNoteListResponse,
  ApiError,
} from '@/types/api';

/**
 * Конфигурация по умолчанию для клиента заметок кандидата
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с заметками кандидата
 *
 * Предоставляет методы для управления заметками кандидата с proper
 * обработкой ошибок и типобезопасностью.
 */
export class CandidateNotesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента заметок кандидата
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
      409: 'Конфликт с существующей заметкой.',
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
   * Создание заметки кандидата
   *
   * @param request - Запрос на создание с деталями заметки
   * @returns Созданная заметка кандидата
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const note = await candidateNotesClient.createNote({
   *   resume_id: 'resume-123',
   *   content: 'Отличный кандидат, сильные технические навыки',
   *   recruiter_id: 'recruiter-123',
   *   is_private: false
   * });
   * ```
   */
  async createNote(request: CandidateNoteCreate): Promise<CandidateNoteResponse> {
    try {
      const response: AxiosResponse<CandidateNoteResponse> = await this.client.post(
        '/api/candidate-notes/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка заметок кандидата с опциональными фильтрами
   *
   * @param resumeId - Опциональный фильтр по ID резюме
   * @param isPrivate - Опциональный фильтр по приватному статусу
   * @param recruiterId - Опциональный фильтр по ID рекрутера (автора)
   * @returns Список заметок кандидата
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех заметок для кандидата
   * const notes = await candidateNotesClient.listNotes('resume-123');
   *
   * // Получение только публичных заметок
   * const publicNotes = await candidateNotesClient.listNotes('resume-123', false);
   *
   * // Получение всех заметок конкретного рекрутера
   * const myNotes = await candidateNotesClient.listNotes(undefined, undefined, 'recruiter-123');
   * ```
   */
  async listNotes(
    resumeId?: string,
    isPrivate?: boolean,
    recruiterId?: string
  ): Promise<CandidateNoteListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (resumeId) params.resume_id = resumeId;
      if (isPrivate !== undefined) params.is_private = isPrivate;
      if (recruiterId) params.recruiter_id = recruiterId;

      const response: AxiosResponse<CandidateNoteListResponse> = await this.client.get(
        '/api/candidate-notes/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение конкретной заметки кандидата по ID
   *
   * @param noteId - ID заметки кандидата
   * @returns Детали заметки кандидата
   * @throws ApiError если заметка не найдена
   *
   * @example
   * ```ts
   * const note = await candidateNotesClient.getNote('note-uuid');
   * ```
   */
  async getNote(noteId: string): Promise<CandidateNoteResponse> {
    try {
      const response: AxiosResponse<CandidateNoteResponse> = await this.client.get(
        `/api/candidate-notes/${noteId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление заметки кандидата
   *
   * @param noteId - ID заметки кандидата
   * @param request - Запрос на обновление с полями для изменения
   * @returns Обновленная заметка кандидата
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await candidateNotesClient.updateNote('note-uuid', {
   *   content: 'Обновленное содержание заметки',
   *   is_private: true
   * });
   * ```
   */
  async updateNote(
    noteId: string,
    request: CandidateNoteUpdate
  ): Promise<CandidateNoteResponse> {
    try {
      const response: AxiosResponse<CandidateNoteResponse> = await this.client.put(
        `/api/candidate-notes/${noteId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление заметки кандидата
   *
   * @param noteId - ID заметки кандидата
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await candidateNotesClient.deleteNote('note-uuid');
   * ```
   */
  async deleteNote(noteId: string): Promise<void> {
    try {
      await this.client.delete(`/api/candidate-notes/${noteId}`);
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
 * Экземпляр клиента заметок кандидата по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с заметками кандидата.
 */
export const candidateNotesClient = new CandidateNotesClient();

/**
 * Экспорт класса заметок кандидата для создания кастомных экземпляров
 */
export default CandidateNotesClient;
