/**
 * Skill Suggestions API Client
 *
 * Этот модуль предоставляет удобный интерфейс для получения предложений навыков
 * на основе индустрии, должности и описания вакансии. Обертывает функциональность
 * предложений навыков классификатора индустрии.
 *
 * @example
 * ```ts
 * import { skillSuggestions } from '@/api/skillSuggestions';
 *
 * // Получение предложений навыков для вакансии
 * const suggestions = await skillSuggestions.getSuggestions({
 *   industry: 'tech',
 *   title: 'Senior React Developer',
 *   description: 'Ищем разработчика React с опытом TypeScript...',
 *   limit: 20,
 * });
 *
 * // Returns: { industry: 'tech', suggested_skills: [...], total_count: 15 }
 * ```
 */

import { industryClassifier } from './industryClassifier';
import type {
  SkillSuggestionRequest,
  SkillSuggestionResponse,
  SkillSuggestionItem,
} from '@/types/api';

/**
 * Конфигурация по умолчанию для предложений навыков
 */
const DEFAULTS = {
  limit: 20,
  minRelevanceScore: 0.3, // Показывать только навыки с релевантностью >= 0.3
};

/**
 * Класс клиента предложений навыков
 *
 * Предоставляет упрощенный интерфейс для получения предложений навыков
 * со встроенной фильтрацией и сортировкой.
 */
export class SkillSuggestionsClient {
  /**
   * Получение предложений навыков на основе индустрии и контекста работы
   *
   * @param request - Параметры запроса предложений
   * @param options - Опциональные переопределения конфигурации
   * @returns Отфильтрованные и отсортированные предложения навыков
   * @throws ApiError если получение предложений не удалось
   *
   * @example
   * ```ts
   * const suggestions = await skillSuggestions.getSuggestions({
   *   industry: 'tech',
   *   title: 'Senior Java Developer',
   *   description: 'Spring, Docker, Kubernetes...',
   *   limit: 20,
   * });
   * ```
   */
  async getSuggestions(
    request: SkillSuggestionRequest,
    options: Partial<typeof DEFAULTS> = {}
  ): Promise<SkillSuggestionResponse> {
    const config = { ...DEFAULTS, ...options };
    const limit = request.limit ?? config.limit;

    try {
      // Получение предложений из API предложений навыков
      const response = await industryClassifier.getAxiosInstance().post(
        '/api/skill-suggestions/suggest',
        {
          ...request,
          limit,
        }
      );

      // Преобразование ответа backend во фронтенд-формат
      const backendData = response.data;

      // Фильтрация по минимальной оценке релевантности и преобразование
      const transformedSkills: SkillSuggestionItem[] = backendData.suggestions
        .filter((s: SkillSuggestionItem) => s.relevance_score >= config.minRelevanceScore)
        .map((s: SkillSuggestionItem) => ({
          skill_name: s.skill_name,
          context: s.context,
          variants: s.variants,
          relevance_score: s.relevance_score,
          category: s.context || undefined,
          is_industry_specific: true, // Все навыки из индустриальной таксономии специфичны для индустрии
        }))
        .sort((a: SkillSuggestionItem, b: SkillSuggestionItem) => b.relevance_score - a.relevance_score);

      return {
        industry: backendData.industry,
        job_title: request.title,
        suggestions: transformedSkills,
        total_count: transformedSkills.length,
      };
    } catch (error) {
      // Переброс ошибки как есть (industryClassifier уже преобразует ее)
      throw error;
    }
  }

  /**
   * Получение только специфичных для индустрии навыков (высокая релевантность)
   *
   * @param request - Параметры запроса предложений
   * @returns Предложения навыков, специфичных для индустрии
   *
   * @example
   * ```ts
   * const industrySkills = await skillSuggestions.getIndustrySpecificSkills({
   *   industry: 'healthcare',
   *   title: 'Registered Nurse',
   *   description: 'Требуется опыт работы в отделении интенсивной терапии...',
   * });
   * ```
   */
  async getIndustrySpecificSkills(
    request: SkillSuggestionRequest
  ): Promise<SkillSuggestionItem[]> {
    const response = await this.getSuggestions(request);

    return response.suggestions.filter((skill) => skill.is_industry_specific);
  }

  /**
   * Получение предложений, сгруппированных по категориям
   *
   * @param request - Параметры запроса предложений
   * @returns Навыки, сгруппированные по категориям
   *
   * @example
   * ```ts
   * const grouped = await skillSuggestions.getSuggestionsByCategory({
   *   industry: 'tech',
   *   title: 'Full Stack Developer',
   * });
   *
   * // Returns: { 'Programming Languages': [...], 'Frameworks': [...], ... }
   * ```
   */
  async getSuggestionsByCategory(
    request: SkillSuggestionRequest
  ): Promise<Record<string, SkillSuggestionItem[]>> {
    const response = await this.getSuggestions(request);

    const grouped: Record<string, SkillSuggestionItem[]> = {};

    for (const skill of response.suggestions) {
      const category = skill.category || 'Other';

      if (!grouped[category]) {
        grouped[category] = [];
      }

      grouped[category].push(skill);
    }

    return grouped;
  }
}

/**
 * Экземпляр клиента предложений навыков по умолчанию
 *
 * Используйте этот singleton-экземпляр для всех вызовов предложений навыков.
 */
export const skillSuggestions = new SkillSuggestionsClient();

/**
 * Экспорт класса клиента предложений навыков для создания кастомных экземпляров
 */
export default SkillSuggestionsClient;
