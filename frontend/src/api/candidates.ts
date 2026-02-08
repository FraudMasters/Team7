/**
 * Candidate API Client
 *
 * Этот модуль предоставляет клиент для работы с кандидатами через микросервис Candidate Service.
 * Поддерживает полный цикл управления кандидатами: просмотр списка, просмотр деталей,
 * перемещение между этапами workflow.
 *
 * @example
 * ```ts
 * import { candidatesClient, CandidatesClient } from '@/api/candidates';
 *
 * // Получение списка всех кандидатов
 * const candidates = await candidatesClient.listCandidates();
 *
 * // Получение кандидата по ID
 * const candidate = await candidatesClient.getCandidate('candidate-123');
 *
 * // Перемещение кандидата на новый этап
 * const result = await candidatesClient.moveCandidate('candidate-123', {
 *   stage_id: 'interview',
 *   vacancy_id: 'vacancy-456',
 *   notes: 'Passed screening'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  CandidateListItem,
  ApiError,
  MoveCandidateRequest,
  MoveCandidateResponse,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  MoveCandidateRequest,
  MoveCandidateResponse,
};

/**
 * Конфигурация по умолчанию для клиента кандидатов
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с кандидатами
 *
 * Предоставляет методы для CRUD-операций с кандидатами с proper
 * обработкой ошибок и типобезопасностью.
 */
export class CandidatesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента кандидатов
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
      404: 'Кандидат не найден.',
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
   * Получение списка всех кандидатов с пагинацией и опциональными фильтрами
   *
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимальное количество записей для возврата
   * @param stageId - Опциональный фильтр по ID этапа workflow
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param tagId - Опциональный фильтр по ID тега (показать кандидатов с этим тегом)
   * @returns Список кандидатов
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение первых 50 кандидатов
   * const candidates = await candidatesClient.listCandidates(0, 50);
   *
   * // Фильтрация по этапу
   * const interviewCandidates = await candidatesClient.listCandidates(0, 50, 'interview');
   *
   * // Фильтрация по вакансии
   * const vacancyCandidates = await candidatesClient.listCandidates(0, 50, undefined, 'vacancy-123');
   *
   * // Фильтрация по тегу
   * const taggedCandidates = await candidatesClient.listCandidates(0, 50, undefined, undefined, 'tag-uuid');
   *
   * // Пагинация
   * const page2 = await candidatesClient.listCandidates(50, 50);
   * ```
   */
  async listCandidates(
    skip: number = 0,
    limit: number = 100,
    stageId?: string,
    vacancyId?: string,
    tagId?: string
  ): Promise<CandidateListItem[]> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (stageId) params.stage_id = stageId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (tagId) params.tag_id = tagId;

      const response: AxiosResponse<CandidateListItem[]> = await this.client.get(
        '/api/candidates',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение кандидата по ID
   *
   * @param id - ID кандидата (resume UUID)
   * @returns Данные кандидата
   * @throws ApiError если кандидат не найден
   *
   * @example
   * ```ts
   * const candidate = await candidatesClient.getCandidate('resume-uuid');
   * console.log(candidate.current_stage, candidate.stage_name);
   * ```
   */
  async getCandidate(id: string): Promise<CandidateListItem> {
    try {
      const response: AxiosResponse<CandidateListItem> = await this.client.get(
        `/api/candidates/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Перемещение кандидата на другой этап workflow
   *
   * Создает новую запись в истории этапов для отслеживания переходов.
   * Это позволяет поддерживать полную историю прогресса кандидата.
   *
   * @param id - ID кандидата (resume UUID)
   * @param data - Данные для перемещения (stage_id, vacancy_id, notes)
   * @returns Результат перемещения с предыдущим и новым этапом
   * @throws ApiError если перемещение не удалось
   *
   * @example
   * ```ts
   * const result = await candidatesClient.moveCandidate('resume-uuid', {
   *   stage_id: 'interview',
   *   vacancy_id: 'vacancy-123',
   *   notes: 'Passed screening'
   * });
   * console.log(result.previous_stage, result.new_stage);
   * ```
   */
  async moveCandidate(id: string, data: MoveCandidateRequest): Promise<MoveCandidateResponse> {
    try {
      const response: AxiosResponse<MoveCandidateResponse> = await this.client.put(
        `/api/candidates/${id}/stage`,
        data
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
 * Экземпляр клиента кандидатов по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с кандидатами.
 */
export const candidatesClient = new CandidatesClient();

/**
 * Экспорт класса кандидатов для создания кастомных экземпляров
 */
export default CandidatesClient;
