/**
 * Saved Searches API Client
 *
 * Этот модуль предоставляет клиент для управления сохраненными поисками,
 * включая создание, чтение, обновление и удаление
 * конфигураций сохраненных поисков.
 *
 * @example
 * ```ts
 * import { savedSearchesClient } from '@/api/savedSearches';
 *
 * // Получение всех сохраненных поисков
 * const searches = await savedSearchesClient.listSavedSearches();
 *
 * // Создание нового сохраненного поиска
 * const newSearch = await savedSearchesClient.createSavedSearch({
 *   name: 'Senior Python разработчики',
 *   query: 'Python AND Django',
 *   filters: { min_experience_years: 5 }
 * });
 *
 * // Обновление сохраненного поиска
 * const updated = await savedSearchesClient.updateSavedSearch('search-id', {
 *   name: 'Обновленное название поиска'
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  SavedSearchCreate,
  SavedSearchUpdate,
  SavedSearchResponse,
  SavedSearchListResponse,
  ApiError,
} from '@/types/api';

/**
 * Конфигурация по умолчанию для клиента сохраненных поисков
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с сохраненными поисками
 *
 * Предоставляет методы для управления конфигурациями сохраненных поисков с proper
 * обработкой ошибок и типобезопасностью.
 */
export class SavedSearchesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента сохраненных поисков
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
      409: 'Сохраненный поиск с таким названием уже существует.',
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
   * Создание сохраненного поиска
   *
   * @param request - Запрос на создание с деталями сохраненного поиска
   * @returns Созданный сохраненный поиск
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const search = await savedSearchesClient.createSavedSearch({
   *   name: 'Senior Python разработчики',
   *   query: 'Python AND Django',
   *   filters: { min_experience_years: 5 }
   * });
   * ```
   */
  async createSavedSearch(request: SavedSearchCreate): Promise<SavedSearchResponse> {
    try {
      const response: AxiosResponse<SavedSearchResponse> = await this.client.post(
        '/api/saved-searches/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка сохраненных поисков с опциональными фильтрами
   *
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимальное количество записей для возврата
   * @param search - Опциональный фильтр по названию (без учета регистра, частичное совпадение)
   * @returns Список сохраненных поисков
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех сохраненных поисков
   * const searches = await savedSearchesClient.listSavedSearches();
   *
   * // Поиск по названию
   * const pythonSearches = await savedSearchesClient.listSavedSearches(0, 100, 'python');
   * ```
   */
  async listSavedSearches(
    skip: number = 0,
    limit: number = 100,
    search?: string
  ): Promise<SavedSearchListResponse> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (search) params.search = search;

      const response: AxiosResponse<SavedSearchListResponse> = await this.client.get(
        '/api/saved-searches/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение конкретного сохраненного поиска по ID
   *
   * @param savedSearchId - ID сохраненного поиска
   * @returns Детали сохраненного поиска
   * @throws ApiError если поиск не найден
   *
   * @example
   * ```ts
   * const search = await savedSearchesClient.getSavedSearch('search-uuid');
   * ```
   */
  async getSavedSearch(savedSearchId: string): Promise<SavedSearchResponse> {
    try {
      const response: AxiosResponse<SavedSearchResponse> = await this.client.get(
        `/api/saved-searches/${savedSearchId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление сохраненного поиска
   *
   * @param savedSearchId - ID сохраненного поиска
   * @param request - Запрос на обновление с полями для изменения
   * @returns Обновленный сохраненный поиск
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await savedSearchesClient.updateSavedSearch('search-uuid', {
   *   name: 'Обновленное название поиска',
   *   query: 'Python OR Django'
   * });
   * ```
   */
  async updateSavedSearch(
    savedSearchId: string,
    request: SavedSearchUpdate
  ): Promise<SavedSearchResponse> {
    try {
      const response: AxiosResponse<SavedSearchResponse> = await this.client.put(
        `/api/saved-searches/${savedSearchId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление сохраненного поиска
   *
   * @param savedSearchId - ID сохраненного поиска
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await savedSearchesClient.deleteSavedSearch('search-uuid');
   * ```
   */
  async deleteSavedSearch(savedSearchId: string): Promise<void> {
    try {
      await this.client.delete(`/api/saved-searches/${savedSearchId}`);
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
 * Экземпляр клиента сохраненных поисков по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с сохраненными поисками.
 */
export const savedSearchesClient = new SavedSearchesClient();

/**
 * Экспорт класса сохраненных поисков для создания кастомных экземпляров
 */
export default SavedSearchesClient;
