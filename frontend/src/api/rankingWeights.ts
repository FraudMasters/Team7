/**
 * Ranking Weights API Client
 *
 * Этот модуль предоставляет клиент для работы с весовыми профилями ранжирования.
 * Поддерживает полный цикл управления профилями: просмотр списка, создание,
 * обновление, удаление, получение пресетов, история версий и предварительный просмотр влияния весов.
 *
 * @example
 * ```ts
 * import { rankingWeightsClient, RankingWeightsClient } from '@/api/rankingWeights';
 *
 * // Получение списка всех профилей
 * const profiles = await rankingWeightsClient.listWeightProfiles();
 *
 * // Создание нового профиля
 * const created = await rankingWeightsClient.createWeightProfile({
 *   name: 'Experience-Focused Profile',
 *   description: 'High experience weight for senior roles',
 *   experience_months_weight: 0.4,
 *   experience_relevance_weight: 0.3,
 *   overall_match_score_weight: 0.3,
 * });
 *
 * // Получение пресетов
 * const presets = await rankingWeightsClient.getPresetProfiles();
 *
 * // Предварительный просмотр влияния весов
 * const preview = await rankingWeightsClient.previewRankingImpact({
 *   vacancy_id: 'vacancy-123',
 *   experience_months_weight: 0.5,
 *   skills_match_ratio_weight: 0.5,
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  RankingWeightProfile,
  RankingWeightProfileCreate,
  RankingWeightProfileUpdate,
  RankingWeightProfileListResponse,
  RankingWeightPresetsResponse,
  RankingWeightVersionHistoryResponse,
  NormalizeRankingWeightsRequest,
  NormalizedRankingWeightsResponse,
  PreviewRankingImpactRequest,
  PreviewRankingImpactResponse,
} from '@/types/rankingWeights';
import type { ApiError } from '@/types/api';

/**
 * Переэкспорт типов для удобства использования
 */
export type {
  RankingWeightProfile,
  RankingWeightProfileCreate,
  RankingWeightProfileUpdate,
  RankingWeightProfileListResponse,
  RankingWeightPresetsResponse,
  RankingWeightVersionHistoryResponse,
  NormalizeRankingWeightsRequest,
  NormalizedRankingWeightsResponse,
  PreviewRankingImpactRequest,
  PreviewRankingImpactResponse,
};

/**
 * Конфигурация по умолчанию для клиента весов ранжирования
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_GATEWAY_URL ?? 'http://localhost:8888',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Класс клиента API для работы с весовыми профилями ранжирования
 *
 * Предоставляет методы для создания, обновления, удаления и применения
 * весовых профилей с proper обработкой ошибок и типобезопасностью.
 */
export class RankingWeightsClient {
  private client: AxiosInstance;

  /**
   * Создание нового экземпляра клиента весов ранжирования
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
   * const profiles = await rankingWeightsClient.listWeightProfiles();
   *
   * // Фильтрация по организации
   * const orgProfiles = await rankingWeightsClient.listWeightProfiles('org-123');
   *
   * // Получение всех пресетов
   * const presets = await rankingWeightsClient.listWeightProfiles(
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
  ): Promise<RankingWeightProfileListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (isPreset !== undefined) params.is_preset = isPreset;
      params.is_active = isActive;

      const response: AxiosResponse<RankingWeightProfileListResponse> = await this.client.get(
        '/api/ranking-weights/profiles',
        { params }
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Получение конкретного весового профиля по ID
   *
   * @param profileId - ID профиля
   * @returns Профиль весов
   * @throws ApiError если профиль не найден или произошла ошибка
   *
   * @example
   * ```ts
   * const profile = await rankingWeightsClient.getWeightProfile('profile-123');
   * console.log(profile.name, profile.experience_months_weight);
   * ```
   */
  async getWeightProfile(profileId: string): Promise<RankingWeightProfile> {
    try {
      const response: AxiosResponse<RankingWeightProfile> = await this.client.get(
        `/api/ranking-weights/profiles/${profileId}`
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Создание нового весового профиля
   *
   * @param data - Данные для создания профиля
   * @returns Созданный профиль весов
   * @throws ApiError если создание не удалось
   *
   * @example
   * ```ts
   * const created = await rankingWeightsClient.createWeightProfile({
   *   name: 'Senior Developer Profile',
   *   description: 'For senior technical positions',
   *   experience_months_weight: 0.35,
   *   skills_match_ratio_weight: 0.35,
   *   overall_match_score_weight: 0.3,
   * });
   * ```
   */
  async createWeightProfile(
    data: RankingWeightProfileCreate
  ): Promise<RankingWeightProfile> {
    try {
      const response: AxiosResponse<RankingWeightProfile> = await this.client.post(
        '/api/ranking-weights/profiles',
        data
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Обновление существующего весового профиля
   *
   * @param profileId - ID профиля для обновления
   * @param data - Данные для обновления (partial)
   * @returns Обновленный профиль весов
   * @throws ApiError если обновление не удалось
   *
   * @example
   * ```ts
   * const updated = await rankingWeightsClient.updateWeightProfile('profile-123', {
   *   experience_months_weight: 0.4,
   *   change_reason: 'Increased focus on experience',
   * });
   * ```
   */
  async updateWeightProfile(
    profileId: string,
    data: RankingWeightProfileUpdate
  ): Promise<RankingWeightProfile> {
    try {
      const response: AxiosResponse<RankingWeightProfile> = await this.client.put(
        `/api/ranking-weights/profiles/${profileId}`,
        data
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Удаление весового профиля (мягкое удаление)
   *
   * @param profileId - ID профиля для удаления
   * @throws ApiError если удаление не удалось
   *
   * @example
   * ```ts
   * await rankingWeightsClient.deleteWeightProfile('profile-123');
   * ```
   */
  async deleteWeightProfile(profileId: string): Promise<void> {
    try {
      await this.client.delete(`/api/ranking-weights/profiles/${profileId}`);
    } catch (error) {
      throw error;
    }
  }

  /**
   * Получение истории версий для профиля весов
   *
   * @param profileId - ID профиля
   * @returns История версий профиля
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const history = await rankingWeightsClient.getVersionHistory('profile-123');
   * console.log(`${history.total_count} versions found`);
   * ```
   */
  async getVersionHistory(profileId: string): Promise<RankingWeightVersionHistoryResponse> {
    try {
      const response: AxiosResponse<RankingWeightVersionHistoryResponse> = await this.client.get(
        `/api/ranking-weights/profiles/${profileId}/history`
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Получение предустановленных профилей весов
   *
   * @returns Список пресетов
   * @throws ApiError если получение не удалось
   *
   * @example
   * ```ts
   * const presets = await rankingWeightsClient.getPresetProfiles();
   * presets.presets.forEach(preset => {
   *   console.log(preset.name, preset.description);
   * });
   * ```
   */
  async getPresetProfiles(): Promise<RankingWeightPresetsResponse> {
    try {
      const response: AxiosResponse<RankingWeightPresetsResponse> = await this.client.get(
        '/api/ranking-weights/presets'
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Нормализация весов ранжирования (сумма = 1.0)
   *
   * @param weights - Веса для нормализации
   * @returns Нормализованные веса
   * @throws ApiError если нормализация не удалась
   *
   * @example
   * ```ts
   * const normalized = await rankingWeightsClient.normalizeWeights({
   *   experience_months_weight: 3,
   *   skills_match_ratio_weight: 2,
   *   overall_match_score_weight: 1,
   * });
   * // Результат: 0.5, 0.33, 0.17
   * ```
   */
  async normalizeWeights(
    weights: NormalizeRankingWeightsRequest
  ): Promise<NormalizedRankingWeightsResponse> {
    try {
      const response: AxiosResponse<NormalizedRankingWeightsResponse> = await this.client.post(
        '/api/ranking-weights/normalize',
        weights
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Предварительный просмотр влияния изменения весов на ранжирование кандидатов
   *
   * @param request - Запрос с ID вакансии и новыми весами
   * @returns Детальная информация о влиянии весов на ранжирование
   * @throws ApiError если предварительный просмотр не удался
   *
   * @example
   * ```ts
   * const preview = await rankingWeightsClient.previewRankingImpact({
   *   vacancy_id: 'vacancy-123',
   *   experience_months_weight: 0.5,
   *   skills_match_ratio_weight: 0.5,
   * });
   * console.log(`${preview.candidates_moved} candidates changed position`);
   * console.log('Top movers:', preview.biggest_movers_up);
   * ```
   */
  async previewRankingImpact(
    request: PreviewRankingImpactRequest
  ): Promise<PreviewRankingImpactResponse> {
    try {
      const response: AxiosResponse<PreviewRankingImpactResponse> = await this.client.post(
        '/api/ranking-weights/preview-impact',
        request
      );
      return response.data;
    } catch (error) {
      throw error;
    }
  }
}

/**
 * Экземпляр клиента по умолчанию для удобства использования
 *
 * @example
 * ```ts
 * import { rankingWeightsClient } from '@/api/rankingWeights';
 *
 * const profiles = await rankingWeightsClient.listWeightProfiles();
 * ```
 */
export const rankingWeightsClient = new RankingWeightsClient();
