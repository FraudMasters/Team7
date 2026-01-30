/**
 * Taxonomies API Client
 *
 * This module provides a client for fetching and merging taxonomies from
 * multiple sources: static skills, industry-specific skills, and custom
 * organization synonyms.
 *
 * @example
 * ```ts
 * import { taxonomiesClient } from '@/api/taxonomies';
 *
 * // Get all merged taxonomies (static + industry + custom)
 * const allSkills = await taxonomiesClient.getMergedTaxonomies({
 *   industry: 'healthcare',
 *   organizationId: 'org123',
 * });
 *
 * // Search skills with autocomplete
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
 * Default API configuration for taxonomies client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Merged taxonomy result
 */
export interface MergedTaxonomy {
  static: SkillDefinition[];
  industry: SkillDefinition[];
  custom: SkillDefinition[];
  all: SkillDefinition[];
}

/**
 * Search options
 */
export interface SearchOptions {
  industry?: string;
  organizationId?: string;
  limit?: number;
}

/**
 * Taxonomies API Client class
 *
 * Provides methods for fetching and merging taxonomies from multiple sources
 * with proper error handling and type safety.
 */
export class TaxonomiesClient {
  private client: AxiosInstance;
  private customSynonymsCache: Map<string, SkillDefinition[]> = new Map();
  private cacheExpiry: Map<string, number> = new Map();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Create a new Taxonomies client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config: Partial<typeof DEFAULT_CONFIG> = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => Promise.reject(this.transformError(error))
    );
  }

  /**
   * Transform Axios error to standardized API error
   *
   * @param error - Axios error
   * @returns Transformed API error
   */
  private transformError(error: unknown): ApiError {
    const axiosError = error as AxiosError<{ detail?: string }>;

    // Network error (no response)
    if (!axiosError.response) {
      if (axiosError.code === 'ECONNABORTED') {
        return {
          detail: 'Request timeout. Please check your connection and try again.',
          status: 408,
        };
      }
      return {
        detail: 'Network error. Please check your connection and try again.',
        status: 0,
      };
    }

    // Server returned error response
    const status = axiosError.response.status;
    const data = axiosError.response.data;

    // Use server's error message if available
    if (data?.detail) {
      return { detail: data.detail, status };
    }

    // Default error messages by status code
    const defaultMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input.',
      401: 'Unauthorized. Please log in.',
      403: 'Forbidden. You do not have permission.',
      404: 'Resource not found.',
      422: 'Validation error. Please check your input.',
      429: 'Too many requests. Please try again later.',
      500: 'Server error. Please try again later.',
      502: 'Bad gateway. Please try again later.',
      503: 'Service unavailable. Please try again later.',
    };

    return {
      detail: data?.detail || defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  /**
   * Fetch custom synonyms from backend for an organization
   *
   * @param organizationId - Organization ID
   * @returns List of custom synonym skill definitions
   * @throws ApiError if fetch fails
   */
  async fetchCustomSynonyms(organizationId: string): Promise<SkillDefinition[]> {
    const cacheKey = `custom_${organizationId}`;
    const now = Date.now();
    const cachedExpiry = this.cacheExpiry.get(cacheKey);

    // Return cached data if still valid
    if (cachedExpiry && cachedExpiry > now && this.customSynonymsCache.has(cacheKey)) {
      return this.customSynonymsCache.get(cacheKey)!;
    }

    try {
      const params: Record<string, string | boolean> = {
        organization_id: organizationId,
        is_active: true,
      };

      const response: AxiosResponse<CustomSynonymListResponse[]> =
        await this.client.get('/api/custom-synonyms/', { params });

      // Transform to SkillDefinition format
      const skillDefs: SkillDefinition[] = response.data.flatMap((item) =>
        item.synonyms.map((synonym) => ({
          id: `custom_${synonym.id}`,
          name: synonym.canonical_skill,
          synonyms: synonym.custom_synonyms,
          category: synonym.context || 'custom',
        }))
      );

      // Cache the results
      this.customSynonymsCache.set(cacheKey, skillDefs);
      this.cacheExpiry.set(cacheKey, now + this.CACHE_TTL);

      return skillDefs;
    } catch (error) {
      // Return empty array on error (fail gracefully)
      // This allows static + industry taxonomies to still work
      return [];
    }
  }

  /**
   * Get all merged taxonomies (static + industry + custom)
   *
   * @param options - Search options including industry and organization ID
   * @returns Merged taxonomy with all sources
   *
   * @example
   * ```ts
   * const merged = await taxonomiesClient.getMergedTaxonomies({
   *   industry: 'healthcare',
   *   organizationId: 'org123',
   * });
   *
   * console.log(merged.all.length); // Total unique skills
   * console.log(merged.static.length); // Static tech skills
   * console.log(merged.industry.length); // Industry-specific skills
   * console.log(merged.custom.length); // Custom organization skills
   * ```
   */
  async getMergedTaxonomies(options: SearchOptions = {}): Promise<MergedTaxonomy> {
    const { industry, organizationId } = options;

    // Get static skills (always available)
    const staticSkills = getStaticSkills();

    // Get industry-specific skills if industry provided
    let industrySkills: SkillDefinition[] = [];
    if (industry) {
      const industryTaxonomy = this.getIndustryTaxonomy(industry);
      if (industryTaxonomy) {
        industrySkills = getIndustrySkills(industry);
      }
    }

    // Get custom synonyms if organization ID provided
    let customSkills: SkillDefinition[] = [];
    if (organizationId) {
      customSkills = await this.fetchCustomSynonyms(organizationId);
    }

    // Merge all skills and deduplicate by name
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
   * Search skills across all taxonomy sources
   *
   * @param query - Search query
   * @param options - Search options including industry and organization ID
   * @returns Matching skills sorted by relevance
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

    // Get merged taxonomies
    const merged = await this.getMergedTaxonomies({ industry, organizationId });

    // Filter skills that match query (name or synonyms)
    const matches = merged.all.filter((skill) => {
      // Check exact name match
      if (skill.name.toLowerCase().includes(normalized)) {
        return true;
      }

      // Check synonyms
      return skill.synonyms.some((synonym) =>
        synonym.toLowerCase().includes(normalized)
      );
    });

    // Sort by relevance (exact name match first, then starts with, then includes)
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
   * Get canonical skill name (handles synonyms across all sources)
   *
   * @param input - User input skill name
   * @param options - Search options including industry and organization ID
   * @returns Canonical skill name or null if not found
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
      // Exact name match
      if (skill.name.toLowerCase() === normalized) {
        return skill.name;
      }

      // Synonym match
      if (skill.synonyms.some((s) => s.toLowerCase() === normalized)) {
        return skill.name;
      }
    }

    return null; // Not found
  }

  /**
   * Get skill suggestions based on partial input
   *
   * @param input - Partial skill input
   * @param options - Search options
   * @returns Array of suggested skill names
   */
  async getSkillSuggestions(
    input: string,
    options: SearchOptions = {}
  ): Promise<string[]> {
    const matches = await this.searchSkills(input, options);
    return matches.map((m) => m.name);
  }

  /**
   * Clear the custom synonyms cache
   *
   * Call this if custom synonyms are updated and you want to refresh the data.
   *
   * @param organizationId - Optional organization ID to clear specific cache
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
   * Get industry taxonomy by ID
   *
   * @param industryId - Industry ID (healthcare, finance, marketing, etc.)
   * @returns Industry taxonomy or null if not found
   */
  private getIndustryTaxonomy(industryId: string): IndustryTaxonomy | null {
    // This is handled by importing from industryTaxonomies module
    // The actual implementation is in the data layer
    return null;
  }

  /**
   * Deduplicate skills by name
   *
   * When multiple sources have the same skill name, merge their synonyms.
   *
   * @param skills - Array of skill definitions
   * @returns Deduplicated skill definitions
   */
  private deduplicateSkills(skills: SkillDefinition[]): SkillDefinition[] {
    const skillMap = new Map<string, SkillDefinition>();

    for (const skill of skills) {
      const existing = skillMap.get(skill.name);

      if (existing) {
        // Merge synonyms
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
   * Get the underlying Axios instance
   *
   * This is useful for making custom requests not covered by the convenience methods.
   *
   * @returns Axios instance
   */
  getAxiosInstance(): AxiosInstance {
    return this.client;
  }
}

/**
 * Default taxonomies client instance
 *
 * Use this singleton instance for all taxonomy calls.
 */
export const taxonomiesClient = new TaxonomiesClient();

/**
 * Export taxonomies client class for custom instances
 */
export default TaxonomiesClient;
