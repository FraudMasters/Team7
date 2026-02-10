/**
 * Job Applications API Client
 *
 * Этот модуль предоставляет клиент для работы с откликами на вакансии.
 * Поддерживает подачу заявки, получение списка своих откликов и просмотр деталей отклика.
 *
 * @example
 * ```ts
 * import { jobApplicationsClient, JobApplicationsClient } from '@/api/jobApplications';
 *
 * // Подача заявки на вакансию
 * const application = await jobApplicationsClient.submitApplication({
 *   vacancy_id: 'vacancy-123',
 *   resume_id: 'resume-456',
 *   email: 'candidate@example.com',
 *   phone: '+1234567890',
 *   cover_letter: 'I am interested in this position because...',
 * });
 *
 * // Получение списка своих заявок
 * const myApplications = await jobApplicationsClient.getMyApplications(0, 20);
 *
 * // Получение заявки по ID
 * const applicationDetails = await jobApplicationsClient.getApplication('app-789');
 *
 * // Фильтрация заявок по статусу
 * const underReview = await jobApplicationsClient.getMyApplications(0, 20, 'under_review');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ApiError,
  JobApplicationSubmitRequest,
  JobApplicationResponse,
  JobApplicationsListResponse,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  JobApplicationSubmitRequest,
  JobApplicationResponse,
  JobApplicationsListResponse,
};

/**
 * Конфигурация по умолчанию для клиента заявок
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с откликами на вакансии
 *
 * Предоставляет методы для подачи заявок, получения списка заявок и просмотра деталей
 * с proper обработкой ошибок и типобезопасностью.
 */
export class JobApplicationsClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента заявок
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
      404: 'Заявка не найдена.',
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
   * Подача заявки на вакансию
   *
   * Позволяет соискателю подать заявку на вакансию. Если пользователь авторизован,
   * заявка привязывается к его аккаунту. Иначе подается как гостевая заявка.
   *
   * @param request - Данные для подачи заявки
   * @returns Созданная заявка с присвоенным ID
   * @throws ApiError если подача заявки не удалась
   *
   * @example
   * ```ts
   * // Подача заявки с резюме
   * const created = await jobApplicationsClient.submitApplication({
   *   vacancy_id: 'vacancy-123',
   *   resume_id: 'resume-456',
   *   email: 'candidate@example.com',
   *   phone: '+1234567890',
   *   cover_letter: 'I am very interested in this position because...',
   * });
   *
   * // Подача заявки без резюме (только с контактными данными)
   * const guest = await jobApplicationsClient.submitApplication({
   *   vacancy_id: 'vacancy-123',
   *   email: 'guest@example.com',
   *   phone: '+9876543210',
   * });
   * ```
   */
  async submitApplication(request: JobApplicationSubmitRequest): Promise<JobApplicationResponse> {
    try {
      const response: AxiosResponse<JobApplicationResponse> = await this.client.post(
        '/api/job-applications/submit',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка заявок текущего пользователя
   *
   * Возвращает список заявок, поданных текущим пользователем, с пагинацией
   * и опциональной фильтрацией по статусу.
   *
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимальное количество записей для возврата
   * @param statusFilter - Опциональный фильтр по статусу заявки
   * @returns Список заявок с метаданными пагинации
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение первых 20 заявок
   * const applications = await jobApplicationsClient.getMyApplications(0, 20);
   *
   * // Фильтрация по статусу
   * const underReview = await jobApplicationsClient.getMyApplications(0, 20, 'under_review');
   *
   * // Пагинация
   * const page2 = await jobApplicationsClient.getMyApplications(20, 20);
   * ```
   */
  async getMyApplications(
    skip: number = 0,
    limit: number = 10,
    statusFilter?: string
  ): Promise<JobApplicationsListResponse> {
    try {
      const params: Record<string, number | string> = { skip, limit };
      if (statusFilter) params.status_filter = statusFilter;

      const response: AxiosResponse<JobApplicationsListResponse> = await this.client.get(
        '/api/job-applications/my-applications',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение заявки по ID
   *
   * Возвращает детали заявки по её ID. Пользователь может просматривать только
   * свои собственные заявки.
   *
   * @param id - ID заявки
   * @returns Данные заявки
   * @throws ApiError если заявка не найдена или нет прав доступа
   *
   * @example
   * ```ts
   * const application = await jobApplicationsClient.getApplication('app-123');
   * console.log(application.status, application.vacancy_title);
   * ```
   */
  async getApplication(id: string): Promise<JobApplicationResponse> {
    try {
      const response: AxiosResponse<JobApplicationResponse> = await this.client.get(
        `/api/job-applications/${id}`
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
 * Экземпляр клиента заявок по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с заявками.
 */
export const jobApplicationsClient = new JobApplicationsClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default JobApplicationsClient;
