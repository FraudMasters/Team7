/**
 * Skill Suggestions API Client
 *
 * This module provides a convenient interface for fetching skill suggestions
 * based on industry, job title, and job description. It wraps the industry
 * classifier's skill suggestion functionality.
 *
 * @example
 * ```ts
 * import { skillSuggestions } from '@/api/skillSuggestions';
 *
 * // Get skill suggestions for a job posting
 * const suggestions = await skillSuggestions.getSuggestions({
 *   industry: 'tech',
 *   title: 'Senior React Developer',
 *   description: 'Looking for a React developer with TypeScript experience...',
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
 * Default configuration for skill suggestions
 */
const DEFAULTS = {
  limit: 20,
  minRelevanceScore: 0.3, // Only show skills with relevance >= 0.3
};

/**
 * Skill Suggestions Client class
 *
 * Provides a simplified interface for fetching skill suggestions
 * with built-in filtering and sorting.
 */
export class SkillSuggestionsClient {
  /**
   * Get skill suggestions based on industry and job context
   *
   * @param request - Suggestion request parameters
   * @param options - Optional configuration overrides
   * @returns Filtered and sorted skill suggestions
   * @throws ApiError if suggestion fails
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
      // Fetch suggestions from the skill suggestions API
      const response = await industryClassifier.getAxiosInstance().post(
        '/api/skill-suggestions/suggest',
        {
          ...request,
          limit,
        }
      );

      // Transform backend response to frontend format
      const backendData = response.data;

      // Filter by minimum relevance score and transform
      const transformedSkills: SkillSuggestionItem[] = backendData.suggestions
        .filter((s: SkillSuggestionItem) => s.relevance_score >= config.minRelevanceScore)
        .map((s: SkillSuggestionItem) => ({
          skill_name: s.skill_name,
          context: s.context,
          variants: s.variants,
          relevance_score: s.relevance_score,
          category: s.context || undefined,
          is_industry_specific: true, // All skills from industry taxonomy are industry-specific
        }))
        .sort((a: SkillSuggestionItem, b: SkillSuggestionItem) => b.relevance_score - a.relevance_score);

      return {
        industry: backendData.industry,
        job_title: request.title,
        suggestions: transformedSkills,
        total_count: transformedSkills.length,
      };
    } catch (error) {
      // Re-throw the error as-is (industryClassifier already transforms it)
      throw error;
    }
  }

  /**
   * Get only industry-specific skills (high relevance)
   *
   * @param request - Suggestion request parameters
   * @returns Industry-specific skill suggestions
   *
   * @example
   * ```ts
   * const industrySkills = await skillSuggestions.getIndustrySpecificSkills({
   *   industry: 'healthcare',
   *   title: 'Registered Nurse',
   *   description: 'ICU experience required...',
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
   * Get suggestions grouped by category
   *
   * @param request - Suggestion request parameters
   * @returns Skills grouped by category
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
 * Default skill suggestions client instance
 *
 * Use this singleton instance for all skill suggestion calls.
 */
export const skillSuggestions = new SkillSuggestionsClient();

/**
 * Export skill suggestions client class for custom instances
 */
export default SkillSuggestionsClient;
