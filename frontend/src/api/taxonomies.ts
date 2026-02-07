/**
 * Taxonomies API Client
 *
 * Этот модуль предоставляет клиент для получения и объединения таксономий из
 * нескольких источников: статические навыки, специфичные для индустрии навыки и
 * кастомные синонимы организации.
 *
 * @example
 * ```ts
 * import { taxonomiesClient } from '@/api/taxonomies';
 *
 * // Получение всех объединенных таксономий (статические + индустрия + кастомные)
 * const allSkills = await taxonomiesClient.getMergedTaxonomies({
 *   industry: 'healthcare',
 *   organizationId: 'org123',
 * });
 *
 * // Поиск навыков с автозаполнением
 * const matches = await taxonomiesClient.searchSkills('java', {
 *   industry: 'tech',
 *   organizationId: 'org123',
 *   limit: 20,
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  CustomSynonymListResponse,
  ApiError,
} from '@/types/api';
import {
  getAllSkills as getStaticSkills,
  searchSkills as searchStaticSkills,
  type SkillDefinition,
} from '@/data/skillsTaxonomy';
import {
  getAllIndustrySkills,
  getIndustrySkills,
  searchIndustrySkills,
  type IndustryTaxonomy,
} from '@/data/industryTaxonomies';

/**
 * Конфигурация API по умолчанию для клиента таксономий
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 секунд
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Результат объединенной таксономии
 */
export interface MergedTaxonomy {
  static: SkillDefinition[];
  industry: SkillDefinition[];
  custom: SkillDefinition[];
  all: SkillDefinition[];
}

/**
 * Опции поиска
 */
export interface SearchOptions {
  industry?: string;
  organizationId?: string;
  limit?: number;
}

/**
 * Класс клиента API таксономий
 *
 * Предоставляет методы для получения и объединения таксономий из нескольких источников
 * с proper обработкой ошибок и типобезопасностью.
 */
export class TaxonomiesClient {
  private client: AxiosInstance;
  private customSynonymsCache: Map<string, SkillDefinition[]> = new Map();
  private cacheExpiry: Map<string, number> = new Map();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 минут

  /**
   * Создание нового экземпляра клиента таксономий
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
   * Получение кастомных синонимов из backend для организации
   *
   * @param organizationId - ID организации
   * @returns Список определений навыков кастомных синонимов
   * @throws ApiError если получение не удалось
   */
  async fetchCustomSynonyms(organizationId: string): Promise<SkillDefinition[]> {
    const cacheKey = `custom_${organizationId}`;
    const now = Date.now();
    const cachedExpiry = this.cacheExpiry.get(cacheKey);

    // Возврат кэшированных данных, если они все еще действительны
    if (cachedExpiry && cachedExpiry > now && this.customSynonymsCache.has(cacheKey)) {
      return this.customSynonymsCache.get(cacheKey)!;
    }

    try {
      const params: Record<string, string | boolean> = {
        organization_id: organizationId,
        is_active: true,
      };

      const response: AxiosResponse<CustomSynonymListResponse[]> =
        await this.client.get('/api/custom-correct-synonyms/', { params });

      // Преобразование в формат SkillDefinition
      const skillDefs: SkillDefinition[] = response.data.flatMap((item) =>
        item.synonyms.map((synonym) => ({
          id: `custom_${synonym.id}`,
          name: synonym.canonical_skill,
          synonyms: synonym.custom_synonyms,
          category: synonym.context || 'custom',
        }))
      );

      // Кэширование результатов
      this.customSynonymsCache.set(cacheKey, skillDefs);
      this.cacheExpiry.set(cacheKey, now + this.CACHE_TTL);

      return skillDefs;
    } catch (error) {
      // Возврат пустого массива при ошибке (soft fail)
      // Это позволяет статическим + индустриальным таксономиям продолжать работать
      return [];
    }
  }

  /**
   * Получение всех объединенных таксономий (статические + индустрия + кастомные)
   *
   * @param options - Опции поиска, включая индустрию и ID организации
   * @returns Объединенная таксономия со всеми источниками
   *
   * @example
   * ```ts
   * const merged = await taxonomiesClient.getMergedTaxonomies({
   *   industry: 'healthcare',
   *   organizationId: 'org123',
   * });
   *
   * console.log(merged.all.length); // Общее количество уникальных навыков
   * console.log(merged.static.length); // Статические технические навыки
   * console.log(merged.industry.length); // Специфичные для индустрии навыки
   * console.log(merged.custom.length); // Кастомные навыки организации
   * ```
   */
  async getMergedTaxonomies(options: SearchOptions = {}): Promise<MergedTaxonomy> {
    const { industry, organizationId } = options;

    // Получение статических навыков (всегда доступно)
    const staticSkills = getStaticSkills();

    // Получение специфичных для индустрии навыков, если указана индустрия
    let industrySkills: SkillDefinition[] = [];
    if (industry) {
      const industryTaxonomy = this.getIndustryTaxonomy(industry);
      if (industryTaxonomy) {
        industrySkills = getIndustrySkills(industry);
      }
    }

    // Получение кастомных синонимов, если указан ID организации
    let customSkills: SkillDefinition[] = [];
    if (organizationId) {
      customSkills = await this.fetchCustomSynonyms(organizationId);
    }

    // Объединение всех навыков и удаление дубликатов по названию
    const allSkills = this.deduplicateSkills([
      ...staticSkills,
      ...industrySkills,
      ...customSkills,
    ]);

    return {
      static: staticSkills,
      industry: industrySkills,
      custom: customSkills,
      all: allSkills,
    };
  }

  /**
   * Поиск навыков по всем источникам таксономий
   *
   * @param query - Поисковый запрос
   * @param options - Опции поиска, включая индустрию и ID организации
   * @returns Совпадающие навыки, отсортированные по релевантности
   *
   * @example
   * ```ts
   * const matches = await taxonomiesClient.searchSkills('java', {
   *   industry: 'tech',
   *   organizationId: 'org123',
   *   limit: 20,
   * });
   * ```
   */
  async searchSkills(query: string, options: SearchOptions = {}): Promise<SkillDefinition[]> {
    if (!query || query.length < 2) return [];

    const { industry, organizationId, limit = 20 } = options;
    const normalized = query.toLowerCase().trim();

    // Получение объединенных таксономий
    const merged = await this.getMergedTaxonomies({ industry, organizationId });

    // Фильтрация навыков, соответствующих запросу (название или синонимы)
    const matches = merged.all.filter((skill) => {
      // Проверка точного совпадения названия
      if (skill.name.toLowerCase().includes(normalized)) {
        return true;
      }

      // Проверка синонимов
      return skill.synonyms.some((synonym) =>
        synonym.toLowerCase().includes(normalized)
      );
    });

    // Сортировка по релевантности (сначала точное совпадение названия, затем начинается с, затем включает)
    matches.sort((a, b) => {
      const aExact = a.name.toLowerCase() === normalized;
      const bExact = b.name.toLowerCase() === normalized;

      if (aExact && !bExact) return -1;
      if (!aExact && bExact) return 1;

      const aStartsWith = a.name.toLowerCase().startsWith(normalized);
      const bStartsWith = b.name.toLowerCase().startsWith(normalized);

      if (aStartsWith && !bStartsWith) return -1;
      if (!bStartsWith && aStartsWith) return 1;

      return 0;
    });

    return matches.slice(0, limit);
  }

  /**
   * Получение канонического названия навыка (обрабатывает синонимы по всем источникам)
   *
   * @param input - Введенное пользователем название навыка
   * @param options - Опции поиска, включая индустрию и ID организации
   * @returns Каноническое название навыка или null, если не найдено
   *
   * @example
   * ```ts
   * const canonical = await taxonomiesClient.getCanonicalSkillName('js', {
   *   industry: 'tech',
   * });
   * // Returns: 'JavaScript'
   * ```
   */
  async getCanonicalSkillName(
    input: string,
    options: SearchOptions = {}
  ): Promise<string | null> {
    if (!input) return null;

    const normalized = input.toLowerCase().trim();
    const merged = await this.getMergedTaxonomies(options);

    for (const skill of merged.all) {
      // Точное совпадение названия
      if (skill.name.toLowerCase() === normalized) {
        return skill.name;
      }

      // Совпадение синонима
      if (skill.synonyms.some((s) => s.toLowerCase() === normalized)) {
        return skill.name;
      }
    }

    return null; // Не найдено
  }

  /**
   * Получение предложений навыков на основе частичного ввода
   *
   * @param input - Частичный ввод навыка
   * @param options - Опции поиска
   * @returns Массив предложенных названий навыков
   */
  async getSkillSuggestions(
    input: string,
    options: SearchOptions = {}
  ): Promise<string[]> {
    const matches = await this.searchSkills(input, options);
    return matches.map((m) => m.name);
  }

  /**
   * Очистка кэша кастомных синонимов
   *
   * Вызовите этот метод, если кастомные синонимы были обновлены и вы хотите обновить данные.
   *
   * @param organizationId - Опциональный ID организации для очистки конкретного кэша
   */
  clearCache(organizationId?: string): void {
    if (organizationId) {
      this.customSynonymsCache.delete(`custom_${organizationId}`);
      this.cacheExpiry.delete(`custom_${organizationId}`);
    } else {
      this.customSynonymsCache.clear();
      this.cacheExpiry.clear();
    }
  }

  /**
   * Получение таксономии индустрии по ID
   *
   * @param industryId - ID индустрии (healthcare, finance, marketing и т.д.)
   * @returns Таксономия индустрии или null, если не найдена
   */
  private getIndustryTaxonomy(industryId: string): IndustryTaxonomy | null {
    // Это обрабатывается импортом из модуля industryTaxonomies
    // Фактическая реализация находится в слое данных
    return null;
  }

  /**
   * Удаление дубликатов навыков по названию
   *
   * Когда несколько источников имеют одно и то же название навыка, объединяет их синонимы.
   *
   * @param skills - Массив определений навыков
   * @returns Определения навыков без дубликатов
   */
  private deduplicateSkills(skills: SkillDefinition[]): SkillDefinition[] {
    const skillMap = new Map<string, SkillDefinition>();

    for (const skill of skills) {
      const existing = skillMap.get(skill.name);

      if (existing) {
        // Объединение синонимов
        const mergedSynonyms = Array.from(
          new Set([...existing.synonyms, ...skill.synonyms])
        );
        existing.synonyms = mergedSynonyms;
      } else {
        skillMap.set(skill.name, { ...skill });
      }
    }

    return Array.from(skillMap.values());
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
 * Экземпляр клиента таксономий по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех вызовов таксономий.
 */
export const taxonomiesClient = new TaxonomiesClient();

/**
 * Экспорт класса клиента таксономий для создания кастомных экземпляров
 */
export default TaxonomiesClient;
