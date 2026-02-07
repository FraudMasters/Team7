/**
 * Matching Weights API Client
 *
 * Этот модуль предоставляет клиент для работы с весовыми профилями матчинга.
 * Поддерживает полный цикл управления профилями: просмотр списка, создание,
 * обновление, удаление, получение пресетов, история версий и применение весов.
 *
 * @example
 * ```ts
 * import { matchingWeightsClient, MatchingWeightsClient } from '@/api/matchingWeights';
 *
 * // Получение списка всех профилей
 * const profiles = await matchingWeightsClient.listWeightProfiles();
 *
 * // Создание нового профиля
 * const created = await matchingWeightsClient.createWeightProfile({
 *   name: 'Technical Profile',
 *   description: 'High keyword weight for technical roles',
 *   keyword_weight: 0.6,
 *   tfidf_weight: 0.25,
 *   vector_weight: 0.15,
 * });
 *
 * // Получение пресетов
 * const presets = await matchingWeightsClient.getPresetProfiles();
 *
 * // Применение весов к вакансии
 * const result = await matchingWeightsClient.applyWeights({
 *   vacancy_id: 'vacancy-123',
 *   profile_id: 'profile-456',
 *   re_match_candidates: true,
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  MatchingWeightsProfile,
  MatchingWeightsCreate,
  MatchingWeightsUpdate,
  MatchingWeightsListResponse,
  PresetsResponse,
  VersionHistoryResponse,
  NormalizeWeightsRequest,
  NormalizedWeightsResponse,
  ApplyWeightsRequest,
  ApplyWeightsResponse,
  ApiError,
} from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  MatchingWeightsProfile,
  MatchingWeightsCreate,
  MatchingWeightsUpdate,
  MatchingWeightsListResponse,
  PresetsResponse,
  VersionHistoryResponse,
  NormalizeWeightsRequest,
  NormalizedWeightsResponse,
  ApplyWeightsRequest,
  ApplyWeightsResponse,
};

/**
 * Конфигурация по умолчанию для клиента весов матчинга
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с весовыми профилями матчинга
 *
 * Предоставляет методы для создания, обновления, удаления и применения
 * весовых профилей с proper обработкой ошибок и типобезопасностью.
 */
export class MatchingWeightsClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента весов матчинга
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
      404: 'Профиль весов не найден.',
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
   * Получение списка всех весовых профилей с фильтрацией
   *
   * @param organizationId - Опциональный фильтр по ID организации
   * @param vacancyId - Опциональный фильтр по ID вакансии
   * @param isPreset - Опциональный фильтр по статусу пресета
   * @param isActive - Опциональный фильтр по активному статусу (по умолчанию: true)
   * @returns Список профилей весов с метаданными
   * @throws ApiError если получение списка не удалось
   *
   * @example
   * ```ts
   * // Получение всех активных профилей
   * const profiles = await matchingWeightsClient.listWeightProfiles();
   *
   * // Фильтрация по организации
   * const orgProfiles = await matchingWeightsClient.listWeightProfiles('org-123');
   *
   * // Получение всех пресетов
   * const presets = await matchingWeightsClient.listWeightProfiles(
   *   undefined,
   *   undefined,
   *   true,
   *   true
   * );
   * ```
   */
  async listWeightProfiles(
    organizationId?: string,
    vacancyId?: string,
    isPreset?: boolean,
    isActive: boolean = true,
  ): Promise<MatchingWeightsListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (isPreset !== undefined) params.is_preset = isPreset;
      params.is_active = isActive;

      const response: AxiosResponse<MatchingWeightsListResponse> = await this.client.get(
        '/api/matching-weights/profiles',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение пресетных весовых профилей
   *
   * Возвращает системные пресеты (Technical, Creative, Executive, Balanced).
   *
   * @returns Пресетные профили
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const presets = await matchingWeightsClient.getPresetProfiles();
   * presets.presets.forEach(p => {
   *   console.log(`${p.name}: ${p.use_case}`);
   * });
   * ```
   */
  async getPresetProfiles(): Promise<PresetsResponse> {
    try {
      const response: AxiosResponse<PresetsResponse> = await this.client.get(
        '/api/matching-weights/profiles/presets'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение весового профиля по ID
   *
   * @param id - ID профиля весов
   * @returns Данные профиля весов
   * @throws ApiError если профиль не найден
   *
   * @example
   * ```ts
   * const profile = await matchingWeightsClient.getWeightProfile('profile-123');
   * console.log(profile.weights_percentage);
   * ```
   */
  async getWeightProfile(id: string): Promise<MatchingWeightsProfile> {
    try {
      const response: AxiosResponse<MatchingWeightsProfile> = await this.client.get(
        `/api/matching-weights/profiles/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Создание кастомного весового профиля
   *
   * Создает новый профиль весов с указанными параметрами.
   * Веса будут автоматически нормализованы, если их сумма не равна 1.0.
   *
   * @param request - Запрос на создание с весами и метаданными
   * @returns Созданный профиль весов
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const profile = await matchingWeightsClient.createWeightProfile({
   *   name: 'My Technical Profile',
   *   description: 'High keyword weight for technical roles',
   *   keyword_weight: 0.6,
   *   tfidf_weight: 0.25,
   *   vector_weight: 0.15,
   *   organization_id: 'org-123',
   * });
   * ```
   */
  async createWeightProfile(request: MatchingWeightsCreate): Promise<MatchingWeightsProfile> {
    try {
      const response: AxiosResponse<MatchingWeightsProfile> = await this.client.post(
        '/api/matching-weights/profiles',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Обновление весового профиля
   *
   * Обновляет указанные поля профиля. При изменении весов
   * создается новая версия в истории изменений.
   *
   * @param id - ID профиля весов
   * @param request - Запрос на обновление с полями для изменения
   * @returns Обновленный профиль весов
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await matchingWeightsClient.updateWeightProfile('profile-123', {
   *   keyword_weight: 0.7,
   *   change_reason: 'Increased keyword weight for senior roles',
   * });
   * ```
   */
  async updateWeightProfile(
    id: string,
    request: MatchingWeightsUpdate,
  ): Promise<MatchingWeightsProfile> {
    try {
      const response: AxiosResponse<MatchingWeightsProfile> = await this.client.put(
        `/api/matching-weights/profiles/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Удаление кастомного весового профиля
   *
   * @param id - ID профиля весов
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await matchingWeightsClient.deleteWeightProfile('profile-123');
   * ```
   */
  async deleteWeightProfile(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/matching-weights/profiles/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Получение истории версий весового профиля
   *
   * @param id - ID профиля весов
   * @returns История версий с записями изменений
   * @throws ApiError если получение истории не удалось
   *
   * @example
   * ```ts
   * const history = await matchingWeightsClient.getWeightProfileHistory('profile-123');
   * history.versions.forEach(v => {
   *   console.log(`Version ${v.version}: ${v.change_reason}`);
   * });
   * ```
   */
  async getWeightProfileHistory(id: string): Promise<VersionHistoryResponse> {
    try {
      const response: AxiosResponse<VersionHistoryResponse> = await this.client.get(
        `/api/matching-weights/profiles/${id}/history`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Нормализация весов, чтобы их сумма равнялась 1.0
   *
   * Полезно для предварительной проверки весов перед созданием профиля.
   *
   * @param request - Веса для нормализации
   * @returns Нормализованные веса
   * @throws ApiError если нормализация не удалась
   *
   * @example
   * ```ts
   * const normalized = await matchingWeightsClient.normalizeWeights({
   *   keyword_weight: 0.5,
   *   tfidf_weight: 0.3,
   *   vector_weight: 0.3, // Sum = 1.1
   * });
   * // Возвращает нормализованные значения, сумма которых равна 1.0
   * console.log(normalized.weights_applied);
   * ```
   */
  async normalizeWeights(request: NormalizeWeightsRequest): Promise<NormalizedWeightsResponse> {
    try {
      const response: AxiosResponse<NormalizedWeightsResponse> = await this.client.post(
        '/api/matching-weights/normalize',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Применение кастомных весов к вакансии
   *
   * Применяет указанный профиль весов или кастомные веса к вакансии.
   * Можно запустить перерасчет матчинга для всех кандидатов.
   *
   * @param request - Запрос на применение с ID вакансии и весами
   * @returns Результат применения с информацией о затронутых кандидатах
   * @throws ApiError если применение не удалось
   *
   * @example
   * ```ts
   * // Применение существующего профиля
   * const result = await matchingWeightsClient.applyWeights({
   *   vacancy_id: 'vacancy-123',
   *   profile_id: 'profile-456',
   *   re_match_candidates: true,
   * });
   *
   * // Применение кастомных весов
   * const result2 = await matchingWeightsClient.applyWeights({
   *   vacancy_id: 'vacancy-123',
   *   weights: {
   *     keyword_weight: 0.5,
   *     tfidf_weight: 0.3,
   *     vector_weight: 0.2,
   *   },
   *   re_match_candidates: true,
   * });
   *
   * console.log(`Candidates affected: ${result.candidates_affected}`);
   * ```
   */
  async applyWeights(request: ApplyWeightsRequest): Promise<ApplyWeightsResponse> {
    try {
      const response: AxiosResponse<ApplyWeightsResponse> = await this.client.post(
        '/api/matching-weights/apply',
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
 * Экземпляр клиента весов матчинга по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех операций с весовыми профилями.
 */
export const matchingWeightsClient = new MatchingWeightsClient();

/**
 * Экспорт класса для создания кастомных экземпляров
 */
export default MatchingWeightsClient;
