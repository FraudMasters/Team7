/**
 * Candidate Search API Client
 *
 * Этот модуль предоставляет клиент для расширенного поиска кандидатов с
 * полнотекстовым поиском, булевыми операторами и мульти-полевой фильтрацией.
 *
 * @example
 * ```ts
 * import { candidateSearchClient } from '@/api/search';
 *
 * // Поиск с запросом и фильтрами
 * const results = await candidateSearchClient.searchCandidates({
 *   query: 'Python AND Django',
 *   filters: {
 *     min_experience_years: 3,
 *     max_experience_years: 10,
 *     location: 'Remote'
 *   },
 *   limit: 10
 * });
 *
 * // Поиск только по навыкам
 * const results = await candidateSearchClient.searchCandidates({
 *   filters: {
 *     skills: ['Python', 'FastAPI'],
 *     min_experience_years: 5
 *   }
 * });
 *
 * // Получение истории поиска
 * const history = await candidateSearchClient.getSearchHistory(0, 20);
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  CandidateSearchRequest,
  CandidateSearchResponse,
  SearchHistoryResponse,
  ApiError,
} from '@/types/api';

/**
 * Конфигурация по умолчанию для клиента поиска кандидатов
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для поиска кандидатов
 *
 * Предоставляет методы для поиска кандидатов с proper
 * обработкой ошибок и типобезопасностью.
 */
export class CandidateSearchClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента поиска кандидатов
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
      400: 'Неверные параметры поиска. Проверьте введенные данные.',
      401: 'Не авторизован. Войдите в систему.',
      403: 'Доступ запрещен. У вас нет прав для выполнения этого действия.',
      404: 'Ресурс не найден.',
      422: 'Ошибка валидации. Проверьте критерии поиска.',
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
   * Поиск кандидатов с расширенными фильтрами
   *
   * Поддерживает полнотекстовый поиск с булевыми операторами (AND, OR, NOT)
   * и мульти-полевую фильтрацию по навыкам, опыту, образованию, локации и т.д.
   *
   * @param request - Запрос на поиск с запросом, фильтрами, пагинацией и сортировкой
   * @returns Результаты поиска со списком кандидатов и метаданными
   * @throws ApiError если поиск не удался
   *
   * @example
   * ```ts
   * // Поиск с булевыми операторами и фильтрами
   * const results = await candidateSearchClient.searchCandidates({
   *   query: 'Python AND Django',
   *   filters: {
   *     min_experience_years: 3,
   *     max_experience_years: 10,
   *     location: 'Remote'
   *   },
   *   limit: 10,
   *   sort_by: 'relevance'
   * });
   *
   * // Фильтрация только по навыкам
   * const results = await candidateSearchClient.searchCandidates({
   *   filters: {
   *     skills: ['Python', 'FastAPI', 'PostgreSQL'],
   *     min_experience_years: 5
   *   }
   * });
   *
   * // Поиск с диапазоном оценки совпадения
   * const results = await candidateSearchClient.searchCandidates({
   *   filters: {
   *     min_match_score: 70,
   *     max_match_score: 100
   *   },
   *   sort_by: 'experience'
   * });
   * ```
   */
  async searchCandidates(request: CandidateSearchRequest = {}): Promise<CandidateSearchResponse> {
    try {
      const response: AxiosResponse<CandidateSearchResponse> = await this.client.post(
        '/api/search/candidates',
        {
          query: request.query ?? null,
          filters: request.filters ?? null,
          skip: request.skip ?? 0,
          limit: request.limit ?? 100,
          sort_by: request.sort_by ?? 'relevance',
        }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение истории поиска с пагинацией
   *
   * Получает ранее выполненные поиски, включая запрос, фильтры,
   * количество результатов и время выполнения. Полезно для просмотра и повторения поисков.
   *
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимальное количество записей для возврата
   * @param recruiterId - Опциональный фильтр по ID рекрутера
   * @returns Записи истории поиска с метаданными пагинации
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * // Получение недавней истории поиска
   * const history = await candidateSearchClient.getSearchHistory(0, 20);
   *
   * // Получение следующей страницы
   * const history = await candidateSearchClient.getSearchHistory(20, 20);
   *
   * // Получение истории для конкретного рекрутера
   * const history = await candidateSearchClient.getSearchHistory(0, 50, 'recruiter-uuid');
   * ```
   */
  async getSearchHistory(
    skip: number = 0,
    limit: number = 50,
    recruiterId?: string
  ): Promise<SearchHistoryResponse> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (recruiterId) params.recruiter_id = recruiterId;

      const response: AxiosResponse<SearchHistoryResponse> = await this.client.get(
        '/api/search/history',
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
 * Экземпляр клиента поиска кандидатов по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций поиска кандидатов.
 */
export const candidateSearchClient = new CandidateSearchClient();

/**
 * Экспорт класса поиска кандидатов для создания кастомных экземпляров
 */
export default CandidateSearchClient;
