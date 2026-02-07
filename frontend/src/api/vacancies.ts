/**
 * Vacancy API Client
 *
 * Этот модуль предоставляет клиент для работы с вакансиями через микросервис Vacancy Service.
 * Поддерживает полный цикл управления вакансиями: создание, просмотр, обновление, удаление и массовый импорт.
 *
 * @example
 * ```ts
 * import { vacanciesClient, VacanciesClient } from '@/api/vacancies';
 *
 * // Получение списка всех вакансий
 * const vacancies = await vacanciesClient.listVacancies();
 *
 * // Получение вакансии по ID
 * const vacancy = await vacanciesClient.getVacancy('vacancy-123');
 *
 * // Создание новой вакансии
 * const created = await vacanciesClient.createVacancy({
 *   position: 'Senior React Developer',
 *   industry: 'tech',
 *   mandatory_requirements: ['React', 'TypeScript', 'Node.js'],
 * });
 *
 * // Обновление вакансии
 * const updated = await vacanciesClient.updateVacancy('vacancy-123', {
 *   position: 'Lead React Developer',
 * });
 *
 * // Удаление вакансии
 * await vacanciesClient.deleteVacancy('vacancy-123');
 *
 * // Массовый импорт вакансий
 * const imported = await vacanciesClient.bulkImport({
 *   vacancies: [
 *     { position: 'Frontend Developer', mandatory_requirements: ['React'] },
 *     { position: 'Backend Developer', mandatory_requirements: ['Python'] },
 *   ],
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  JobVacancy,
  ApiError,
  VacancyCreate,
  VacancyUpdate,
  VacancyResponse,
  VacancyListResponse,
  VacancyBulkImportRequest,
  VacancyBulkImportResponse,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  VacancyCreate,
  VacancyUpdate,
  VacancyResponse,
  VacancyListResponse,
  VacancyBulkImportRequest,
  VacancyBulkImportResponse,
};

/**
 * Конфигурация по умолчанию для клиента вакансий
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с вакансиями
 *
 * Предоставляет методы для CRUD-операций с вакансиями с proper
 * обработкой ошибок и типобезопасностью.
 */
export class VacanciesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента вакансий
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
      404: 'Вакансия не найдена.',
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
   * Получение списка всех вакансий с пагинацией и опциональными фильтрами
   *
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимальное количество записей для возврата
   * @param industry - Опциональный фильтр по индустрии
   * @param position - Опциональный фильтр по должности (частичное совпадение)
   * @returns Список вакансий с метаданными пагинации
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение первых 50 вакансий
   * const vacancies = await vacanciesClient.listVacancies(0, 50);
   *
   * // Фильтрация по индустрии
   * const techVacancies = await vacanciesClient.listVacancies(0, 50, 'tech');
   *
   * // Поиск по должности
   * const reactJobs = await vacanciesClient.listVacancies(0, 50, undefined, 'React');
   *
   * // Пагинация
   * const page2 = await vacanciesClient.listVacancies(50, 50);
   * ```
   */
  async listVacancies(
    skip: number = 0,
    limit: number = 100,
    industry?: string,
    position?: string
  ): Promise<VacancyListResponse> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (industry) params.industry = industry;
      if (position) params.position = position;

      const response: AxiosResponse<VacancyListResponse> = await this.client.get(
        '/api/vacancies',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение вакансии по ID
   *
   * @param id - ID вакансии
   * @returns Данные вакансии
   * @throws ApiError если вакансия не найдена
   *
   * @example
   * ```ts
   * const vacancy = await vacanciesClient.getVacancy('vacancy-123');
   * console.log(vacancy.position, vacancy.mandatory_requirements);
   * ```
   */
  async getVacancy(id: string): Promise<VacancyResponse> {
    try {
      const response: AxiosResponse<VacancyResponse> = await this.client.get(
        `/api/vacancies/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Создание новой вакансии
   *
   * @param data - Данные для создания вакансии
   * @returns Созданная вакансия с присвоенным ID
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const created = await vacanciesClient.createVacancy({
   *   position: 'Senior React Developer',
   *   industry: 'tech',
   *   mandatory_requirements: ['React', 'TypeScript', 'Node.js'],
   *   additional_requirements: ['GraphQL', 'Docker'],
   *   experience_levels: ['Senior', 'Lead'],
   * });
   * ```
   */
  async createVacancy(data: VacancyCreate): Promise<VacancyResponse> {
    try {
      const response: AxiosResponse<VacancyResponse> = await this.client.post(
        '/api/vacancies',
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление существующей вакансии
   *
   * @param id - ID вакансии
   * @param data - Данные для обновления (все поля опциональны)
   * @returns Обновленная вакансия
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await vacanciesClient.updateVacancy('vacancy-123', {
   *   position: 'Lead React Developer',
   *   mandatory_requirements: ['React', 'TypeScript', 'Node.js', 'GraphQL'],
   * });
   * ```
   */
  async updateVacancy(id: string, data: VacancyUpdate): Promise<VacancyResponse> {
    try {
      const response: AxiosResponse<VacancyResponse> = await this.client.put(
        `/api/vacancies/${id}`,
        data
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление вакансии
   *
   * @param id - ID вакансии
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await vacanciesClient.deleteVacancy('vacancy-123');
   * ```
   */
  async deleteVacancy(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/vacancies/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Массовый импорт вакансий
   *
   * Позволяет создать несколько вакансий за один запрос.
   * Возвращает результаты импорта с разделением на успешные и неудачные.
   *
   * @param request - Запрос с массивом вакансий для импорта
   * @returns Результаты импорта с подсчетом успешных и неудачных
   * @throws ApiError если импорт не удалось выполнить
   *
   * @example
   * ```ts
   * const result = await vacanciesClient.bulkImport({
   *   vacancies: [
   *     {
   *       position: 'Frontend Developer',
   *       industry: 'tech',
   *       mandatory_requirements: ['React', 'TypeScript'],
   *     },
   *     {
   *       position: 'Backend Developer',
   *       industry: 'tech',
   *       mandatory_requirements: ['Python', 'Django', 'PostgreSQL'],
   *     },
   *     {
   *       position: 'DevOps Engineer',
   *       industry: 'tech',
   *       mandatory_requirements: ['Docker', 'Kubernetes', 'AWS'],
   *     },
   *   ],
   * });
   *
   * console.log(`Импортировано: ${result.total_imported}`);
   * console.log(`Ошибок: ${result.total_failed}`);
   * result.failed.forEach(({ vacancy, error }) => {
   *   console.error(`Ошибка для ${vacancy.position}: ${error}`);
   * });
   * ```
   */
  async bulkImport(request: VacancyBulkImportRequest): Promise<VacancyBulkImportResponse> {
    try {
      const response: AxiosResponse<VacancyBulkImportResponse> = await this.client.post(
        '/api/vacancies/bulk',
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
 * Экземпляр клиента вакансий по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с вакансиями.
 */
export const vacanciesClient = new VacanciesClient();

/**
 * Экспорт класса вакансий для создания кастомных экземпляров
 */
export default VacanciesClient;
