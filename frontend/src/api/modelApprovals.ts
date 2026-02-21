/**
 * Model Approvals API Client
 *
 * Этот модуль предоставляет клиент для работы с workflow одобрения ML-моделей через API Gateway.
 * Поддерживает полный цикл управления запросами на развертывание: создание, просмотр списка,
 * одобрение, отклонение, отмену и развертывание моделей.
 *
 * @example
 * ```ts
 * import { modelApprovalsClient, ModelApprovalsClient } from '@/api/modelApprovals';
 *
 * // Создание запроса на развертывание модели
 * const approval = await modelApprovalsClient.createApprovalRequest({
 *   model_version_id: 'version-123',
 *   justification: 'Improved accuracy by 5%',
 *   target_environment: 'production',
 *   organization_id: 'org-1',
 *   requested_by: 'user-1',
 * });
 *
 * // Получение списка запросов
 * const approvals = await modelApprovalsClient.listApprovals({ status: 'pending' });
 *
 * // Одобрение запроса
 * const approved = await modelApprovalsClient.approveRequest('approval-123', {
 *   reviewed_by: 'admin-1',
 *   review_notes: 'Approved after thorough review',
 * });
 *
 * // Отклонение запроса
 * const rejected = await modelApprovalsClient.rejectRequest('approval-123', {
 *   reviewed_by: 'admin-1',
 *   review_notes: 'Insufficient testing data',
 * });
 *
 * // Отмена запроса
 * const cancelled = await modelApprovalsClient.cancelRequest('approval-123');
 *
 * // Развертывание одобренной модели
 * const deployed = await modelApprovalsClient.deployRequest('approval-123');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ModelApprovalCreate,
  ModelApprovalUpdate,
  ModelApprovalAction,
  ModelApprovalResponse,
  ModelApprovalListResponse,
  ModelApprovalDetailResponse,
  ModelApprovalAuditLogResponse,
  ModelApprovalStatsResponse,
  ModelApprovalDashboardResponse,
  ModelApprovalListParams,
  ModelApprovalDeployResponse,
  ApiError,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  ModelApprovalCreate,
  ModelApprovalUpdate,
  ModelApprovalAction,
  ModelApprovalResponse,
  ModelApprovalListResponse,
  ModelApprovalDetailResponse,
  ModelApprovalAuditLogResponse,
  ModelApprovalStatsResponse,
  ModelApprovalDashboardResponse,
  ModelApprovalListParams,
  ModelApprovalDeployResponse,
};

/**
 * Конфигурация по умолчанию для клиента одобрения моделей
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 30000, // 30 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с одобрением моделей
 *
 * Предоставляет методы для создания, просмотра, одобрения, отклонения,
 * отмены и развертывания запросов на развертывание ML-моделей с proper
 * обработкой ошибок и типобезопасностью.
 */
export class ModelApprovalsClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента одобрения моделей
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
      404: 'Запрос на одобрение не найден.',
      409: 'Конфликт. Возможно, запрос уже существует.',
      422: 'Ошибка валидации. Проверьте входные данные.',
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
   * Создание запроса на развертывание модели
   *
   * @param request - Запрос на создание с данными модели
   * @returns Созданный запрос на одобрение
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const approval = await modelApprovalsClient.createApprovalRequest({
   *   model_version_id: 'version-123',
   *   justification: 'Improved accuracy by 5%',
   *   target_environment: 'production',
   *   organization_id: 'org-1',
   *   requested_by: 'user-1',
   * });
   * console.log('Создан запрос:', approval.id);
   * ```
   */
  async createApprovalRequest(request: ModelApprovalCreate): Promise<ModelApprovalResponse> {
    try {
      const response: AxiosResponse<ModelApprovalResponse> = await this.client.post(
        '/api/model-approvals/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка запросов на одобрение с опциональными фильтрами
   *
   * @param params - Опциональные параметры фильтрации
   * @returns Список запросов на одобрение
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех запросов
   * const allApprovals = await modelApprovalsClient.listApprovals();
   *
   * // Фильтрация по статусу
   * const pending = await modelApprovalsClient.listApprovals({ status: 'pending' });
   *
   * // Фильтрация по организации
   * const orgApprovals = await modelApprovalsClient.listApprovals({ organization_id: 'org-1' });
   *
   * // Фильтрация по имени модели
   * const modelApprovals = await modelApprovalsClient.listApprovals({ model_name: 'skill_matching' });
   * ```
   */
  async listApprovals(params?: ModelApprovalListParams): Promise<ModelApprovalListResponse> {
    try {
      const response: AxiosResponse<ModelApprovalListResponse> = await this.client.get(
        '/api/model-approvals/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение запроса на одобрение по ID
   *
   * @param id - ID запроса на одобрение
   * @returns Данные запроса на одобрение
   * @throws ApiError если запрос не найден
   *
   * @example
   * ```ts
   * const approval = await modelApprovalsClient.getApproval('approval-123');
   * console.log('Статус:', approval.status);
   * console.log('Модель:', approval.model_name);
   * ```
   */
  async getApproval(id: string): Promise<ModelApprovalResponse> {
    try {
      const response: AxiosResponse<ModelApprovalResponse> = await this.client.get(
        `/api/model-approvals/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Одобрение запроса на развертывание модели
   *
   * Одобряет запрос на развертывание, изменяя его статус на 'approved'.
   * Только запросы в статусе 'pending' могут быть одобрены.
   *
   * @param id - ID запроса на одобрение
   * @param action - Данные действия с информацией о ревьюере
   * @returns Обновленный запрос на одобрение
   * @throws ApiError если одобрение не удалось
   *
   * @example
   * ```ts
   * const approved = await modelApprovalsClient.approveRequest('approval-123', {
   *   reviewed_by: 'admin-1',
   *   review_notes: 'Approved after thorough review',
   * });
   * console.log('Запрос одобрен:', approved.status === 'approved');
   * ```
   */
  async approveRequest(id: string, action: ModelApprovalAction): Promise<ModelApprovalResponse> {
    try {
      const response: AxiosResponse<ModelApprovalResponse> = await this.client.post(
        `/api/model-approvals/${id}/approve`,
        action
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Отклонение запроса на развертывание модели
   *
   * Отклоняет запрос на развертывание, изменяя его статус на 'rejected'.
   * Только запросы в статусе 'pending' могут быть отклонены.
   *
   * @param id - ID запроса на одобрение
   * @param action - Данные действия с информацией о ревьюере
   * @returns Обновленный запрос на одобрение
   * @throws ApiError если отклонение не удалось
   *
   * @example
   * ```ts
   * const rejected = await modelApprovalsClient.rejectRequest('approval-123', {
   *   reviewed_by: 'admin-1',
   *   review_notes: 'Insufficient testing data',
   * });
   * console.log('Запрос отклонен:', rejected.status === 'rejected');
   * ```
   */
  async rejectRequest(id: string, action: ModelApprovalAction): Promise<ModelApprovalResponse> {
    try {
      const response: AxiosResponse<ModelApprovalResponse> = await this.client.post(
        `/api/model-approvals/${id}/reject`,
        action
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Отмена запроса на развертывание модели
   *
   * Отменяет запрос на развертывание, изменяя его статус на 'cancelled'.
   * Только запросы в статусе 'pending' могут быть отменены.
   *
   * @param id - ID запроса на одобрение
   * @returns Обновленный запрос на одобрение
   * @throws ApiError если отмена не удалась
   *
   * @example
   * ```ts
   * const cancelled = await modelApprovalsClient.cancelRequest('approval-123');
   * console.log('Запрос отменен:', cancelled.status === 'cancelled');
   * ```
   */
  async cancelRequest(id: string): Promise<ModelApprovalResponse> {
    try {
      const response: AxiosResponse<ModelApprovalResponse> = await this.client.post(
        `/api/model-approvals/${id}/cancel`,
        {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Развертывание одобренной модели
   *
   * Развертывает одобренную модель в целевой среде, изменяя статус на 'deployed'
   * и активируя модель в производстве. Только запросы в статусе 'approved'
   * могут быть развернуты.
   *
   * @param id - ID запроса на одобрение
   * @returns Обновленный запрос с информацией о развертывании
   * @throws ApiError если развертывание не удалось
   *
   * @example
   * ```ts
   * const deployed = await modelApprovalsClient.deployRequest('approval-123');
   * console.log('Модель развернута:', deployed.deployment_status);
   * console.log('Модель активирована:', deployed.model_activated);
   * ```
   */
  async deployRequest(id: string): Promise<ModelApprovalDeployResponse> {
    try {
      const response: AxiosResponse<ModelApprovalDeployResponse> = await this.client.post(
        `/api/model-approvals/${id}/deploy`,
        {}
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
 * Экземпляр клиента одобрения моделей по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с одобрением моделей.
 */
export const modelApprovalsClient = new ModelApprovalsClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default ModelApprovalsClient;
