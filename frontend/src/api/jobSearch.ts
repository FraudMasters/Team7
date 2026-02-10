/**
 * Job Search API Client
 *
 * Этот модуль предоставляет клиент для поиска вакансий через микросервис Vacancy Service.
 * Поддерживает полнотекстовый поиск по должности и описанию, фильтрацию по нескольким критериям,
 * пагинацию и сортировку результатов.
 *
 * @example
 * ```ts
 * import { jobSearchClient, JobSearchClient } from '@/api/jobSearch';
 *
 * // Поиск вакансий с запросом
 * const results = await jobSearchClient.searchJobs({
 *   query: 'Python developer',
 *   limit: 20,
 * });
 *
 * // Поиск с фильтрами
 * const remoteJobs = await jobSearchClient.searchJobs({
 *   query: 'React',
 *   filters: {
 *     location: 'Remote',
 *     salary_min: 50000,
 *     work_format: 'remote',
 *   },
 *   limit: 50,
 * });
 *
 * // Фильтрация по навыкам
 * const pythonJobs = await jobSearchClient.searchJobs({
 *   filters: {
 *     skills: ['Python', 'FastAPI', 'PostgreSQL'],
 *     employment_type: 'full-time',
 *   },
 *   sort_by: 'salary_desc',
 * });
 *
 * // Пагинация
 * const page2 = await jobSearchClient.searchJobs({
 *   skip: 20,
 *   limit: 20,
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ApiError,
  JobSearchRequest,
  JobSearchResponse,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  JobSearchRequest,
  JobSearchResponse,
};

/**
 * Конфигурация по умолчанию для клиента поиска вакансий
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для поиска вакансий
 *
 * Предоставляет методы для поиска вакансий с proper обработкой ошибок
 * и типобезопасностью.
 */
export class JobSearchClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента поиска вакансий
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
   * Поиск вакансий с помощью POST-запроса
   *
   * Это основной метод поиска, поддерживающий все параметры:
   * полнотекстовый поиск, фильтрацию, пагинацию и сортировку.
   *
   * @param request - Параметры поиска вакансий
   * @returns Результаты поиска с метаданными
   * @throws ApiError если поиск не удался
   *
   * @example
   * ```ts
   * // Базовый поиск по запросу
   * const results = await jobSearchClient.searchJobs({
   *   query: 'Python developer',
   *   limit: 20,
   * });
   *
   * // Поиск с множественными фильтрами
   * const filtered = await jobSearchClient.searchJobs({
   *   query: 'Frontend',
   *   filters: {
   *     location: 'Remote',
   *     salary_min: 60000,
   *     salary_max: 120000,
   *     work_format: 'remote',
   *     employment_type: 'full-time',
   *     skills: ['React', 'TypeScript'],
   *   },
   *   skip: 0,
   *   limit: 50,
   *   sort_by: 'salary_desc',
   * });
   * ```
   */
  async searchJobs(request: JobSearchRequest = {}): Promise<JobSearchResponse> {
    try {
      const {
        query = null,
        filters = null,
        skip = 0,
        limit = 100,
        sort_by = 'date',
      } = request;

      const requestBody = {
        query,
        filters,
        skip,
        limit,
        sort_by,
      };

      const response: AxiosResponse<JobSearchResponse> = await this.client.post(
        '/api/job-search/search',
        requestBody
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Поиск вакансий с помощью GET-запроса
   *
   * Альтернативный метод поиска, использующий query-параметры вместо JSON тела.
   * Удобен для простых поисковых запросов и запросов из браузера.
   *
   * @param request - Параметры поиска вакансий
   * @returns Результаты поиска с метаданными
   * @throws ApiError если поиск не удался
   *
   * @example
   * ```ts
   * // Простой поиск через GET
   * const results = await jobSearchClient.searchJobsGet({
   *   query: 'Java developer',
   *   limit: 20,
   * });
   *
   * // Поиск с фильтрами через query-параметры
   * const remote = await jobSearchClient.searchJobsGet({
   *   location: 'Remote',
   *   salary_min: 50000,
   *   work_format: 'remote',
   * });
   * ```
   */
  async searchJobsGet(request: JobSearchRequest = {}): Promise<JobSearchResponse> {
    try {
      const {
        query = null,
        filters = null,
        skip = 0,
        limit = 100,
        sort_by = 'date',
      } = request;

      const params: Record<string, string | number> = { skip, limit, sort_by };

      if (query) {
        params.query = query;
      }

      if (filters) {
        if (filters.location) params.location = filters.location;
        if (filters.salary_min !== undefined) params.salary_min = filters.salary_min;
        if (filters.salary_max !== undefined) params.salary_max = filters.salary_max;
        if (filters.work_format) params.work_format = filters.work_format;
        if (filters.employment_type) params.employment_type = filters.employment_type;
        if (filters.industry) params.industry = filters.industry;
        if (filters.skills && filters.skills.length > 0) {
          params.skills = filters.skills.join(',');
        }
      }

      const response: AxiosResponse<JobSearchResponse> = await this.client.get(
        '/api/job-search/search',
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
 * Экземпляр клиента поиска вакансий по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций поиска.
 */
export const jobSearchClient = new JobSearchClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default JobSearchClient;
