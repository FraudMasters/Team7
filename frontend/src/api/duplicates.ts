/**
 * Duplicates API Client
 *
 * Этот модуль предоставляет клиент для работы с дубликатами кандидатов через API.
 * Поддерживает обнаружение дубликатов, управление очередью проверки и слияние профилей.
 *
 * @example
 * ```ts
 * import { duplicatesClient, DuplicatesClient } from '@/api/duplicates';
 *
 * // Проверка на дубликаты перед загрузкой
 * const check = await duplicatesClient.checkDuplicate('sha256hash', 'org-123');
 *
 * // Получение списка потенциальных дубликатов
 * const duplicates = await duplicatesClient.listDuplicates('org-123');
 *
 * // Слияние кандидатов
 * const result = await duplicatesClient.mergeCandidates({
 *   primary_id: 'resume-1',
 *   duplicate_id: 'resume-2'
 * });
 *
 * // Получение очереди проверки
 * const queue = await duplicatesClient.listReviewQueue('org-123');
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';

/**
 * Модель для одного совпадения дубликата
 */
export interface DuplicateMatch {
  /** ID совпадающего резюме */
  resume_id: string;
  /** Имя файла совпадающего резюме */
  filename: string;
  /** Время обнаружения дубликата */
  detection_timestamp: string;
  /** Статус резюме */
  status: string;
}

/**
 * Запрос на проверку дубликатов перед загрузкой
 */
export interface PreUploadCheckRequest {
  /** SHA-256 хеш содержимого файла */
  content_hash: string;
  /** ID организации */
  organization_id: string;
  /** Оригинальное имя файла (опционально) */
  filename?: string;
}

/**
 * Ответ на проверку дубликатов перед загрузкой
 */
export interface PreUploadCheckResponse {
  /** Найдены ли дубликаты */
  is_duplicate: boolean;
  /** Количество найденных дубликатов */
  duplicate_count: number;
  /** Список совпадающих резюме */
  matches: DuplicateMatch[];
  /** Сообщение ответа */
  message: string;
}

/**
 * Элемент списка дубликатов
 */
export interface DuplicateResumeItem {
  /** Уникальный идентификатор записи дубликата */
  id: string;
  /** ID организации */
  organization_id: string;
  /** ID оригинального резюме */
  original_resume_id: string;
  /** ID дубликата резюме */
  duplicate_resume_id: string;
  /** Имя файла оригинального резюме */
  original_filename?: string;
  /** Имя файла дубликата резюме */
  duplicate_filename?: string;
  /** SHA-256 хеш дубликата */
  content_hash: string;
  /** Время обнаружения дубликата */
  detection_timestamp: string;
  /** ID пакетного задания, если из пакетной загрузки */
  batch_job_id?: string;
}

/**
 * Ответ на запрос списка дубликатов
 */
export interface DuplicateListResponse {
  /** Список пар дубликатов резюме */
  duplicates: DuplicateResumeItem[];
  /** Общее количество пар дубликатов */
  total_count: number;
  /** ID организации */
  organization_id: string;
}

/**
 * Запрос на слияние кандидатов
 */
export interface MergeCandidatesRequest {
  /** UUID основного резюме для сохранения */
  primary_id: string;
  /** UUID дубликата резюме для слияния */
  duplicate_id: string;
  /** Опциональная причина слияния */
  reason?: string;
  /** ID пользователя, выполняющего слияние */
  merged_by_user_id?: string;
}

/**
 * Ответ на запрос слияния кандидатов
 */
export interface MergeCandidatesResponse {
  /** UUID записи истории слияния */
  merge_id: string;
  /** UUID основного резюме */
  primary_resume_id: string;
  /** UUID дубликата резюме */
  duplicate_resume_id: string;
  /** Время выполнения слияния */
  merge_timestamp: string;
  /** Сообщение об успехе */
  message: string;
  /** Можно ли отменить это слияние */
  can_undo: boolean;
}

/**
 * Элемент очереди проверки
 */
export interface ReviewQueueItem {
  /** ID элемента очереди проверки */
  id: string;
  /** ID организации */
  organization_id: string;
  /** ID оригинального резюме */
  original_resume_id: string;
  /** ID дубликата резюме */
  duplicate_resume_id: string;
  /** Имя файла оригинального резюме */
  original_filename?: string;
  /** Имя файла дубликата резюме */
  duplicate_filename?: string;
  /** Оценка уверенности сходства (0.0 - 1.0) */
  confidence_score: number;
  /** Статус проверки (pending, in_review, approved, rejected) */
  status: string;
  /** ID назначенного проверяющего */
  assigned_reviewer_id?: string;
  /** Время добавления дубликата в очередь */
  queue_entered_at: string;
  /** Время начала проверки */
  review_started_at?: string;
  /** Время завершения проверки */
  review_completed_at?: string;
  /** Причина одобрения/отклонения */
  decision_reason?: string;
  /** ID пакетного задания, если из пакетной загрузки */
  batch_job_id?: string;
  /** Часы ожидания в очереди */
  wait_time_hours?: number;
  /** Время создания записи */
  created_at: string;
  /** Время обновления записи */
  updated_at: string;
}

/**
 * Ответ на запрос списка очереди проверки
 */
export interface ReviewQueueListResponse {
  /** Общее количество элементов, соответствующих фильтрам */
  total: number;
  /** Элементы очереди проверки */
  items: ReviewQueueItem[];
  /** Количество пропущенных элементов */
  skip: number;
  /** Максимальное количество возвращаемых элементов */
  limit: number;
}

/**
 * Запрос на одобрение дубликата
 */
export interface ApproveReviewRequest {
  /** Опциональная причина одобрения */
  decision_reason?: string;
  /** ID пользователя, одобряющего дубликат */
  reviewer_id?: string;
}

/**
 * Ответ на запрос одобрения дубликата
 */
export interface ApproveReviewResponse {
  /** ID элемента очереди проверки */
  id: string;
  /** Новый статус (approved) */
  status: string;
  /** Время завершения проверки */
  review_completed_at: string;
  /** Сообщение об успехе */
  message: string;
}

/**
 * Запрос на отклонение дубликата
 */
export interface RejectReviewRequest {
  /** Опциональная причина отклонения */
  decision_reason?: string;
  /** ID пользователя, отклоняющего дубликат */
  reviewer_id?: string;
}

/**
 * Ответ на запрос отклонения дубликата
 */
export interface RejectReviewResponse {
  /** ID элемента очереди проверки */
  id: string;
  /** Новый статус (rejected) */
  status: string;
  /** Время завершения проверки */
  review_completed_at: string;
  /** Сообщение об успехе */
  message: string;
}

/**
 * Ответ на запрос сканирования существующих данных
 */
export interface ScanExistingResponse {
  /** Общее количество просканированных резюме */
  total_scanned: number;
  /** Количество найденных дубликатов */
  duplicates_found: number;
  /** Количество записанных дубликатов */
  duplicates_recorded: number;
  /** Количество ошибок */
  errors: number;
  /** Сообщение о результате */
  message: string;
  /** ID организации */
  organization_id: string;
}

/**
 * Стандартная ошибка API
 */
export interface ApiError {
  /** Детальное описание ошибки */
  detail: string;
  /** Код статуса HTTP */
  status: number;
}

/**
 * Конфигурация по умолчанию для клиента дубликатов
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с дубликатами
 *
 * Предоставляет методы для обнаружения дубликатов, управления очередью проверки
 * и слияния профилей кандидатов с proper обработкой ошибок и типобезопасностью.
 */
export class DuplicatesClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента дубликатов
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
      404: 'Дубликат не найден.',
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
   * Проверка на дубликаты перед загрузкой
   *
   * Позволяет проверить, существует ли уже резюме с таким же хешем содержимого
   * в системе перед загрузкой. Это предотвращает загрузку дубликатов и
   * предоставляет информацию о существующих совпадающих резюме.
   *
   * @param contentHash - SHA-256 хеш содержимого файла
   * @param organizationId - ID организации
   * @param filename - Оригинальное имя файла (опционально)
   * @returns Результат проверки на дубликаты
   * @throws ApiError если проверка не удалась
   *
   * @example
   * ```ts
   * // Вычисление SHA-256 хеша содержимого файла
   * const hash = await calculateFileHash(file);
   *
   * // Проверка на дубликаты
   * const check = await duplicatesClient.checkDuplicate(hash, 'org-123', 'resume.pdf');
   * if (check.is_duplicate) {
   *   console.log(`Найдено ${check.duplicate_count} дубликатов`);
   *   check.matches.forEach(match => {
   *     console.log(`Существующий файл: ${match.filename}`);
   *   });
   * }
   * ```
   */
  async checkDuplicate(
    contentHash: string,
    organizationId: string,
    filename?: string
  ): Promise<PreUploadCheckResponse> {
    try {
      const request: PreUploadCheckRequest = {
        content_hash: contentHash,
        organization_id: organizationId,
        filename,
      };

      const response: AxiosResponse<PreUploadCheckResponse> = await this.client.post(
        '/api/duplicates/check',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение списка потенциальных дубликатов
   *
   * Возвращает список всех обнаруженных дубликатов резюме для организации
   * с пагинацией.
   *
   * @param organizationId - ID организации
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимальное количество записей для возврата
   * @returns Список дубликатов
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение первых 50 дубликатов
   * const duplicates = await duplicatesClient.listDuplicates('org-123', 0, 50);
   * console.log(`Найдено ${duplicates.total_count} пар дубликатов`);
   *
   * // Пагинация
   * const page2 = await duplicatesClient.listDuplicates('org-123', 50, 50);
   * ```
   */
  async listDuplicates(
    organizationId: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<DuplicateListResponse> {
    try {
      const params: Record<string, number | string> = {
        organization_id: organizationId,
        skip,
        limit,
      };

      const response: AxiosResponse<DuplicateListResponse> = await this.client.get(
        '/api/duplicates',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Слияние профилей кандидатов
   *
   * Объединяет два профиля кандидатов в один, сохраняя основной профиль
   * и объединяя данные из дубликата. Создает запись истории слияния
   * для аудита и возможности отмены.
   *
   * @param request - Параметры слияния (ID основного и дубликата резюме)
   * @returns Результат слияния
   * @throws ApiError если слияние не удалось
   *
   * @example
   * ```ts
   * const result = await duplicatesClient.mergeCandidates({
   *   primary_id: 'resume-1',
   *   duplicate_id: 'resume-2',
   *   reason: 'Confirmed duplicate by manual review',
   *   merged_by_user_id: 'user-123'
   * });
   *
   * console.log(`Слияние выполнено: ${result.message}`);
   * console.log(`ID слияния: ${result.merge_id}`);
   * console.log(`Можно отменить: ${result.can_undo}`);
   * ```
   */
  async mergeCandidates(request: MergeCandidatesRequest): Promise<MergeCandidatesResponse> {
    try {
      const response: AxiosResponse<MergeCandidatesResponse> = await this.client.post(
        '/api/duplicates/merge',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение очереди проверки дубликатов
   *
   * Возвращает список дубликатов, ожидающих ручной проверки, с опциональной
   * фильтрацией по статусу, оценке уверенности и проверяющему.
   *
   * @param organizationId - ID организации
   * @param skip - Количество записей для пропуска (пагинация)
   * @param limit - Максимальное количество записей для возврата
   * @param status - Опциональный фильтр по статусу
   * @param minConfidence - Минимальная оценка уверенности (0.0 - 1.0)
   * @param maxConfidence - Максимальная оценка уверенности (0.0 - 1.0)
   * @param reviewerId - ID проверяющего для фильтрации
   * @param sortBy - Поле для сортировки
   * @param sortOrder - Порядок сортировки (asc или desc)
   * @returns Список элементов очереди проверки
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех ожидающих проверки
   * const pending = await duplicatesClient.listReviewQueue('org-123', 0, 50, 'pending');
   *
   * // Фильтрация по оценке уверенности
   * const lowConfidence = await duplicatesClient.listReviewQueue(
   *   'org-123',
   *   0,
   *   50,
   *   'pending',
   *   0.3,
   *   0.7
   * );
   *
   * // Сортировка по времени ожидания
   * const byWaitTime = await duplicatesClient.listReviewQueue(
   *   'org-123',
   *   0,
   *   50,
   *   undefined,
   *   undefined,
   *   undefined,
   *   undefined,
   *   'wait_time',
   *   'desc'
   * );
   * ```
   */
  async listReviewQueue(
    organizationId: string,
    skip: number = 0,
    limit: number = 100,
    status?: string,
    minConfidence?: number,
    maxConfidence?: number,
    reviewerId?: string,
    sortBy?: string,
    sortOrder?: 'asc' | 'desc'
  ): Promise<ReviewQueueListResponse> {
    try {
      const params: Record<string, number | string> = {
        organization_id: organizationId,
        skip,
        limit,
      };
      if (status) params.status = status;
      if (minConfidence !== undefined) params.min_confidence = minConfidence;
      if (maxConfidence !== undefined) params.max_confidence = maxConfidence;
      if (reviewerId) params.reviewer_id = reviewerId;
      if (sortBy) params.sort_by = sortBy;
      if (sortOrder) params.sort_order = sortOrder;

      const response: AxiosResponse<ReviewQueueListResponse> = await this.client.get(
        '/api/duplicates/review-queue',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Одобрение дубликата в очереди проверки
   *
   * Одобряет пару дубликатов как подтвержденный дубликат, готовый к слиянию.
   * Обновляет статус на "approved" и записывает информацию о проверяющем.
   *
   * @param reviewId - ID элемента очереди проверки
   * @param request - Опциональные параметры одобрения
   * @returns Результат одобрения
   * @throws ApiError если одобрение не удалось
   *
   * @example
   * ```ts
   * const result = await duplicatesClient.approveReview('review-123', {
   *   decision_reason: 'Confirmed same person after manual verification',
   *   reviewer_id: 'user-456'
   * });
   *
   * console.log(`Статус: ${result.status}`);
   * console.log(`Завершено: ${result.review_completed_at}`);
   * ```
   */
  async approveReview(
    reviewId: string,
    request: ApproveReviewRequest = {}
  ): Promise<ApproveReviewResponse> {
    try {
      const response: AxiosResponse<ApproveReviewResponse> = await this.client.post(
        `/api/duplicates/review-queue/${reviewId}/approve`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Отклонение дубликата в очереди проверки
   *
   * Отклоняет пару как не являющуюся дубликатом. Обновляет статус на "rejected"
   * и записывает причину отклонения.
   *
   * @param reviewId - ID элемента очереди проверки
   * @param request - Опциональные параметры отклонения
   * @returns Результат отклонения
   * @throws ApiError если отклонение не удалось
   *
   * @example
   * ```ts
   * const result = await duplicatesClient.rejectReview('review-123', {
   *   decision_reason: 'Different people with similar names',
   *   reviewer_id: 'user-456'
   * });
   *
   * console.log(`Статус: ${result.status}`);
   * ```
   */
  async rejectReview(
    reviewId: string,
    request: RejectReviewRequest = {}
  ): Promise<RejectReviewResponse> {
    try {
      const response: AxiosResponse<RejectReviewResponse> = await this.client.post(
        `/api/duplicates/review-queue/${reviewId}/reject`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Сканирование существующей базы данных на дубликаты
   *
   * Запускает полное сканирование всех существующих резюме в организации
   * для обнаружения дубликатов. Полезно для очистки существующих данных.
   *
   * @param organizationId - ID организации
   * @returns Результат сканирования
   * @throws ApiError если сканирование не удалось
   *
   * @example
   * ```ts
   * const result = await duplicatesClient.scanExisting('org-123');
   * console.log(`Просканировано: ${result.total_scanned}`);
   * console.log(`Найдено дубликатов: ${result.duplicates_found}`);
   * console.log(`Записано: ${result.duplicates_recorded}`);
   * console.log(`Ошибок: ${result.errors}`);
   * ```
   */
  async scanExisting(organizationId: string): Promise<ScanExistingResponse> {
    try {
      const response: AxiosResponse<ScanExistingResponse> = await this.client.post(
        '/api/duplicates/scan-existing',
        { organization_id: organizationId }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

/**
 * Экземпляр клиента дубликатов по умолчанию
 *
 * Готовый к использованию экземпляр клиента с конфигурацией по умолчанию.
 * Для большинства случаев рекомендуется использовать этот экземпляр.
 *
 * @example
 * ```ts
 * import { duplicatesClient } from '@/api/duplicates';
 *
 * const duplicates = await duplicatesClient.listDuplicates('org-123');
 * ```
 */
export const duplicatesClient = new DuplicatesClient();

/**
 * Переэкспорт класса для создания пользовательских экземпляров
 */
export default DuplicatesClient;
