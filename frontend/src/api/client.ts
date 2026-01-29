/**
 * API Client for Resume Analysis Backend
 *
 * This module provides a typed Axios client for communicating with the
 * backend resume analysis service. Handles resume upload, analysis,
 * job matching, skill taxonomies, custom synonyms, feedback, model versions,
 * resume comparisons, and health check endpoints.
 *
 * @example
 * ```ts
 * import { apiClient } from '@/api/client';
 *
 * // Upload resume
 * const uploadResult = await apiClient.uploadResume(file);
 *
 * // Analyze resume
 * const analysis = await apiClient.analyzeResume(uploadResult.id);
 *
 * // Compare with job vacancy
 * const match = await apiClient.compareWithVacancy(resumeId, vacancyData);
 *
 * // Compare multiple resumes
 * const comparison = await apiClient.compareMultipleResumes({
 *   vacancy_id: 'vacancy-123',
 *   resume_ids: ['resume1', 'resume2', 'resume3'],
 * });
 *
 * // Create custom synonyms
 * const synonyms = await apiClient.createCustomSynonyms({
 *   organization_id: 'org123',
 *   synonyms: [{ canonical_skill: 'React', custom_synonyms: ['ReactJS'], is_active: true }],
 * });
 *
 * // Submit feedback
 * const feedback = await apiClient.submitMatchFeedback({
 *   match_id: 'match123',
 *   skill: 'React',
 *   was_correct: true,
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type {
  ResumeUploadResponse,
  AnalysisRequest,
  AnalysisResponse,
  JobVacancy,
  MatchResponse,
  HealthResponse,
  UploadProgressCallback,
  ApiClientConfig,
  ApiError,
  SkillTaxonomyCreate,
  SkillTaxonomyUpdate,
  SkillTaxonomyResponse,
  SkillTaxonomyListResponse,
  CustomSynonymCreate,
  CustomSynonymUpdate,
  CustomSynonymResponse,
  CustomSynonymListResponse,
  FeedbackCreate,
  FeedbackUpdate,
  FeedbackResponse,
  FeedbackListResponse,
  ModelVersionCreate,
  ModelVersionUpdate,
  ModelVersionResponse,
  ModelVersionListResponse,
  MatchFeedbackRequest,
  MatchFeedbackResponse,
  ComparisonCreate,
  ComparisonUpdate,
  ComparisonResponse,
  ComparisonListResponse,
  CompareMultipleRequest,
  ComparisonMatrixData,
  KeyMetricsResponse,
  FunnelMetricsResponse,
  SkillDemandResponse,
  SourceTrackingResponse,
  RecruiterPerformanceResponse,
  LanguagePreferenceUpdate,
  LanguagePreferenceResponse,
} from '@/types/api';

/**
 * Default API configuration
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 120000, // 2 minutes for long-running analysis
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * API Client class
 *
 * Provides methods for all backend API endpoints with proper error handling,
 * type safety, and progress tracking for file uploads.
 */
export class ApiClient {
  private client: AxiosInstance;

  /**
   * Create a new API client instance
   *
   * @param config - Optional configuration overrides
   */
  constructor(config: ApiClientConfig = {}) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };

    this.client = axios.create(finalConfig);

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add timestamp for debugging
        config.metadata = { startTime: Date.now() };
        return config;
      },
      (error) => {
        return Promise.reject(this.transformError(error));
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Calculate request duration
        const duration = Date.now() - (response.config.metadata?.startTime || 0);
        response.config.metadata = { ...response.config.metadata, duration };
        return response;
      },
      (error) => {
        return Promise.reject(this.transformError(error));
      }
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
      413: 'File too large. Please upload a smaller file.',
      415: 'Unsupported file type. Please upload PDF or DOCX.',
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
   * Upload a resume file
   *
   * @param file - Resume file (PDF or DOCX)
   * @param onProgress - Optional progress callback (0-100)
   * @returns Upload response with resume ID
   * @throws ApiError if upload fails
   *
   * @example
   * ```ts
   * const result = await apiClient.uploadResume(file, (progress) => {
   *   console.log(`Upload progress: ${progress}%`);
   * });
   * ```
   */
  async uploadResume(
    file: File,
    onProgress?: UploadProgressCallback
  ): Promise<ResumeUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response: AxiosResponse<ResumeUploadResponse> = await this.client.post(
        '/api/resumes/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total && onProgress) {
              const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              onProgress(progress);
            }
          },
        }
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Analyze a resume
   *
   * @param request - Analysis request with resume ID and options
   * @returns Analysis results with keywords, entities, grammar, and experience
   * @throws ApiError if analysis fails
   *
   * @example
   * ```ts
   * const analysis = await apiClient.analyzeResume({
   *   resume_id: 'abc-123',
   *   extract_experience: true,
   *   check_grammar: true,
   * });
   * ```
   */
  async analyzeResume(request: AnalysisRequest): Promise<AnalysisResponse> {
    try {
      const response: AxiosResponse<AnalysisResponse> = await this.client.post(
        '/api/resumes/analyze',
        request
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Compare resume with job vacancy
   *
   * @param resumeId - Resume ID to compare
   * @param vacancy - Job vacancy data
   * @returns Match results with skill comparison and experience verification
   * @throws ApiError if comparison fails
   *
   * @example
   * ```ts
   * const match = await apiClient.compareWithVacancy('abc-123', {
   *   data: {
   *     position: 'Java Developer',
   *     mandatory_requirements: ['Java', 'Spring', 'SQL'],
   *   },
   * });
   * ```
   */
  async compareWithVacancy(resumeId: string, vacancy: JobVacancy): Promise<MatchResponse> {
    try {
      const response: AxiosResponse<MatchResponse> = await this.client.post(
        '/api/matching/compare',
        {
          resume_id: resumeId,
          vacancy_data: vacancy,
        }
      );

      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Check backend health status
   *
   * @returns Health status
   * @throws ApiError if health check fails
   */
  async healthCheck(): Promise<HealthResponse> {
    try {
      const response: AxiosResponse<HealthResponse> = await this.client.get('/health');
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Check if backend is ready
   *
   * @returns Ready status
   * @throws ApiError if check fails
   */
  async readyCheck(): Promise<{ status: string }> {
    try {
      const response: AxiosResponse<{ status: string }> = await this.client.get('/ready');
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
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

  // ==================== Skill Taxonomies ====================

  /**
   * Create skill taxonomy entries for an industry
   *
   * @param request - Create request with industry and list of skills
   * @returns Created taxonomy entries
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const result = await apiClient.createSkillTaxonomies({
   *   industry: 'tech',
   *   skills: [
   *     {
   *       name: 'React',
   *       context: 'web_framework',
   *       variants: ['React', 'ReactJS', 'React.js'],
   *       is_active: true,
   *     },
   *   ],
   * });
   * ```
   */
  async createSkillTaxonomies(
    request: SkillTaxonomyCreate
  ): Promise<SkillTaxonomyListResponse> {
    try {
      const response: AxiosResponse<SkillTaxonomyListResponse> = await this.client.post(
        '/api/skill-taxonomies/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List skill taxonomies with optional filters
   *
   * @param industry - Optional industry filter
   * @param isActive - Optional active status filter
   * @returns List of skill taxonomy entries
   * @throws ApiError if listing fails
   */
  async listSkillTaxonomies(
    industry?: string,
    isActive?: boolean
  ): Promise<SkillTaxonomyListResponse[]> {
    try {
      const params: Record<string, string | boolean> = {};
      if (industry) params.industry = industry;
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<SkillTaxonomyListResponse[]> =
        await this.client.get('/api/skill-taxonomies/', { params });
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific skill taxonomy entry by ID
   *
   * @param id - Taxonomy entry ID
   * @returns Skill taxonomy entry
   * @throws ApiError if not found
   */
  async getSkillTaxonomy(id: string): Promise<SkillTaxonomyResponse> {
    try {
      const response: AxiosResponse<SkillTaxonomyResponse> = await this.client.get(
        `/api/skill-taxonomies/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a skill taxonomy entry
   *
   * @param id - Taxonomy entry ID
   * @param request - Update request
   * @returns Updated taxonomy entry
   * @throws ApiError if update fails
   */
  async updateSkillTaxonomy(
    id: string,
    request: SkillTaxonomyUpdate
  ): Promise<SkillTaxonomyResponse> {
    try {
      const response: AxiosResponse<SkillTaxonomyResponse> = await this.client.put(
        `/api/skill-taxonomies/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a specific skill taxonomy entry
   *
   * @param id - Taxonomy entry ID
   * @throws ApiError if deletion fails
   */
  async deleteSkillTaxonomy(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/skill-taxonomies/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete all skill taxonomies for an industry
   *
   * @param industry - Industry sector
   * @throws ApiError if deletion fails
   */
  async deleteSkillTaxonomiesByIndustry(industry: string): Promise<void> {
    try {
      await this.client.delete(`/api/skill-taxonomies/industry/${industry}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Custom Synonyms ====================

  /**
   * Create custom synonym entries for an organization
   *
   * @param request - Create request with organization_id and list of synonyms
   * @returns Created synonym entries
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const result = await apiClient.createCustomSynonyms({
   *   organization_id: 'org123',
   *   created_by: 'user456',
   *   synonyms: [
   *     {
   *       canonical_skill: 'React',
   *       custom_synonyms: ['ReactJS', 'React.js', 'React Framework'],
   *       context: 'web_framework',
   *       is_active: true,
   *     },
   *   ],
   * });
   * ```
   */
  async createCustomSynonyms(
    request: CustomSynonymCreate
  ): Promise<CustomSynonymListResponse> {
    try {
      const response: AxiosResponse<CustomSynonymListResponse> = await this.client.post(
        '/api/custom-synonyms/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List custom synonyms with optional filters
   *
   * @param organizationId - Optional organization ID filter
   * @param canonicalSkill - Optional canonical skill filter
   * @param isActive - Optional active status filter
   * @returns List of custom synonym entries
   * @throws ApiError if listing fails
   */
  async listCustomSynonyms(
    organizationId?: string,
    canonicalSkill?: string,
    isActive?: boolean
  ): Promise<CustomSynonymListResponse[]> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (canonicalSkill) params.canonical_skill = canonicalSkill;
      if (isActive !== undefined) params.is_active = isActive;

      const response: AxiosResponse<CustomSynonymListResponse[]> =
        await this.client.get('/api/custom-synonyms/', { params });
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific custom synonym entry by ID
   *
   * @param id - Synonym entry ID
   * @returns Custom synonym entry
   * @throws ApiError if not found
   */
  async getCustomSynonym(id: string): Promise<CustomSynonymResponse> {
    try {
      const response: AxiosResponse<CustomSynonymResponse> = await this.client.get(
        `/api/custom-synonyms/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a custom synonym entry
   *
   * @param id - Synonym entry ID
   * @param request - Update request
   * @returns Updated synonym entry
   * @throws ApiError if update fails
   */
  async updateCustomSynonym(
    id: string,
    request: CustomSynonymUpdate
  ): Promise<CustomSynonymResponse> {
    try {
      const response: AxiosResponse<CustomSynonymResponse> = await this.client.put(
        `/api/custom-synonyms/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a specific custom synonym entry
   *
   * @param id - Synonym entry ID
   * @throws ApiError if deletion fails
   */
  async deleteCustomSynonym(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/custom-synonyms/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete all custom synonyms for an organization
   *
   * @param organizationId - Organization ID
   * @throws ApiError if deletion fails
   */
  async deleteCustomSynonymsByOrganization(organizationId: string): Promise<void> {
    try {
      await this.client.delete(`/api/custom-synonyms/organization/${organizationId}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Feedback ====================

  /**
   * Create feedback entries
   *
   * @param request - Create request with list of feedback entries
   * @returns Created feedback entries
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const result = await apiClient.createFeedback({
   *   feedback: [
   *     {
   *       resume_id: 'abc123',
   *       vacancy_id: 'vac456',
   *       skill: 'React',
   *       was_correct: true,
   *       confidence_score: 0.95,
   *       feedback_source: 'frontend',
   *     },
   *   ],
   * });
   * ```
   */
  async createFeedback(request: FeedbackCreate): Promise<FeedbackListResponse> {
    try {
      const response: AxiosResponse<FeedbackListResponse> = await this.client.post(
        '/api/feedback/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List feedback entries with optional filters
   *
   * @param resumeId - Optional resume ID filter
   * @param vacancyId - Optional vacancy ID filter
   * @param skill - Optional skill filter
   * @param wasCorrect - Optional correctness filter
   * @param processed - Optional processed status filter
   * @param feedbackSource - Optional feedback source filter
   * @returns List of feedback entries
   * @throws ApiError if listing fails
   */
  async listFeedback(
    resumeId?: string,
    vacancyId?: string,
    skill?: string,
    wasCorrect?: boolean,
    processed?: boolean,
    feedbackSource?: string
  ): Promise<FeedbackListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (resumeId) params.resume_id = resumeId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (skill) params.skill = skill;
      if (wasCorrect !== undefined) params.was_correct = wasCorrect;
      if (processed !== undefined) params.processed = processed;
      if (feedbackSource) params.feedback_source = feedbackSource;

      const response: AxiosResponse<FeedbackListResponse> = await this.client.get(
        '/api/feedback/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific feedback entry by ID
   *
   * @param id - Feedback entry ID
   * @returns Feedback entry
   * @throws ApiError if not found
   */
  async getFeedback(id: string): Promise<FeedbackResponse> {
    try {
      const response: AxiosResponse<FeedbackResponse> = await this.client.get(
        `/api/feedback/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a feedback entry
   *
   * @param id - Feedback entry ID
   * @param request - Update request
   * @returns Updated feedback entry
   * @throws ApiError if update fails
   */
  async updateFeedback(
    id: string,
    request: FeedbackUpdate
  ): Promise<FeedbackResponse> {
    try {
      const response: AxiosResponse<FeedbackResponse> = await this.client.put(
        `/api/feedback/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a specific feedback entry
   *
   * @param id - Feedback entry ID
   * @throws ApiError if deletion fails
   */
  async deleteFeedback(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/feedback/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Model Versions ====================

  /**
   * Create model version entries
   *
   * @param request - Create request with list of model versions
   * @returns Created model version entries
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const result = await apiClient.createModelVersions({
   *   models: [
   *     {
   *       model_name: 'skill_matching',
   *       version: 'v2.0.0',
   *       is_active: false,
   *       is_experiment: true,
   *       experiment_config: { traffic_percentage: 20 },
   *       performance_score: 92.5,
   *     },
   *   ],
   * });
   * ```
   */
  async createModelVersions(
    request: ModelVersionCreate
  ): Promise<ModelVersionListResponse> {
    try {
      const response: AxiosResponse<ModelVersionListResponse> = await this.client.post(
        '/api/model-versions/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List model versions with optional filters
   *
   * @param modelName - Optional model name filter
   * @param isActive - Optional active status filter
   * @param isExperiment - Optional experiment status filter
   * @returns List of model version entries
   * @throws ApiError if listing fails
   */
  async listModelVersions(
    modelName?: string,
    isActive?: boolean,
    isExperiment?: boolean
  ): Promise<ModelVersionListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (modelName) params.model_name = modelName;
      if (isActive !== undefined) params.is_active = isActive;
      if (isExperiment !== undefined) params.is_experiment = isExperiment;

      const response: AxiosResponse<ModelVersionListResponse> = await this.client.get(
        '/api/model-versions/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get the active model by name
   *
   * @param modelName - Model name
   * @returns Active model version
   * @throws ApiError if not found
   */
  async getActiveModel(modelName: string): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.get(
        `/api/model-versions/active`,
        { params: { model_name: modelName } }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific model version by ID
   *
   * @param id - Model version ID
   * @returns Model version entry
   * @throws ApiError if not found
   */
  async getModelVersion(id: string): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.get(
        `/api/model-versions/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a model version
   *
   * @param id - Model version ID
   * @param request - Update request
   * @returns Updated model version
   * @throws ApiError if update fails
   */
  async updateModelVersion(
    id: string,
    request: ModelVersionUpdate
  ): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.put(
        `/api/model-versions/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a specific model version
   *
   * @param id - Model version ID
   * @throws ApiError if deletion fails
   */
  async deleteModelVersion(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/model-versions/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Activate a model version
   *
   * @param id - Model version ID
   * @returns Updated model version
   * @throws ApiError if activation fails
   */
  async activateModelVersion(id: string): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.post(
        `/api/model-versions/${id}/activate`,
        {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Deactivate a model version
   *
   * @param id - Model version ID
   * @returns Updated model version
   * @throws ApiError if deactivation fails
   */
  async deactivateModelVersion(id: string): Promise<ModelVersionResponse> {
    try {
      const response: AxiosResponse<ModelVersionResponse> = await this.client.post(
        `/api/model-versions/${id}/deactivate`,
        {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Matching Feedback ====================

  /**
   * Submit feedback on a skill match result
   *
   * @param request - Feedback request with match_id, skill, and correctness
   * @returns Created feedback entry
   * @throws ApiError if submission fails
   *
   * @example
   * ```ts
   * const result = await apiClient.submitMatchFeedback({
   *   match_id: 'match123',
   *   skill: 'React',
   *   was_correct: true,
   *   confidence_score: 0.95,
   * });
   * ```
   */
  async submitMatchFeedback(request: MatchFeedbackRequest): Promise<MatchFeedbackResponse> {
    try {
      const response: AxiosResponse<MatchFeedbackResponse> = await this.client.post(
        '/api/matching/feedback',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Comparisons ====================

  /**
   * Create a new resume comparison view
   *
   * @param request - Create request with vacancy_id, resume_ids, and optional settings
   * @returns Created comparison view
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const result = await apiClient.createComparison({
   *   vacancy_id: 'vacancy-123',
   *   resume_ids: ['resume1', 'resume2', 'resume3'],
   *   name: 'Senior Developer Candidates',
   *   filters: { min_match_percentage: 50 },
   * });
   * ```
   */
  async createComparison(request: ComparisonCreate): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.post(
        '/api/comparisons/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List resume comparison views with optional filters and sorting
   *
   * @param vacancyId - Optional vacancy ID filter
   * @param createdBy - Optional creator user ID filter
   * @param minMatchPercentage - Optional minimum match percentage filter (0-100)
   * @param maxMatchPercentage - Optional maximum match percentage filter (0-100)
   * @param sortBy - Sort field - created_at, match_percentage, name, or updated_at
   * @param order - Sort order - asc or desc
   * @param limit - Maximum number of results to return (default: 50, max: 100)
   * @param offset - Number of results to skip (default: 0)
   * @returns List of comparison views
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const result = await apiClient.listComparisons(
   *   'vacancy-123',
   *   undefined,
   *   50,
   *   90,
   *   'match_percentage',
   *   'desc',
   *   10,
   *   0
   * );
   * ```
   */
  async listComparisons(
    vacancyId?: string,
    createdBy?: string,
    minMatchPercentage?: number,
    maxMatchPercentage?: number,
    sortBy?: string,
    order?: string,
    limit?: number,
    offset?: number
  ): Promise<ComparisonListResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (vacancyId) params.vacancy_id = vacancyId;
      if (createdBy) params.created_by = createdBy;
      if (minMatchPercentage !== undefined) params.min_match_percentage = minMatchPercentage;
      if (maxMatchPercentage !== undefined) params.max_match_percentage = maxMatchPercentage;
      if (sortBy) params.sort_by = sortBy;
      if (order) params.order = order;
      if (limit !== undefined) params.limit = limit;
      if (offset !== undefined) params.offset = offset;

      const response: AxiosResponse<ComparisonListResponse> = await this.client.get(
        '/api/comparisons/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific comparison view by ID
   *
   * @param id - Comparison view ID
   * @returns Comparison view details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const comparison = await apiClient.getComparison('comp-123');
   * ```
   */
  async getComparison(id: string): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.get(
        `/api/comparisons/${id}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a comparison view
   *
   * @param id - Comparison view ID
   * @param request - Update request with fields to modify
   * @returns Updated comparison view
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await apiClient.updateComparison('comp-123', {
   *   name: 'Updated Comparison Name',
   *   filters: { min_match_percentage: 60 },
   * });
   * ```
   */
  async updateComparison(
    id: string,
    request: ComparisonUpdate
  ): Promise<ComparisonResponse> {
    try {
      const response: AxiosResponse<ComparisonResponse> = await this.client.put(
        `/api/comparisons/${id}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a comparison view
   *
   * @param id - Comparison view ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await apiClient.deleteComparison('comp-123');
   * ```
   */
  async deleteComparison(id: string): Promise<void> {
    try {
      await this.client.delete(`/api/comparisons/${id}`);
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Compare multiple resumes against a job vacancy
   *
   * This endpoint performs intelligent matching between each resume's skills
   * and the job vacancy requirements, handling synonyms (e.g., PostgreSQL ≈ SQL)
   * and providing aggregated results with ranking by match percentage.
   *
   * @param request - Compare request with vacancy_id and resume_ids
   * @returns Comparison matrix data with ranked results
   * @throws ApiError if comparison fails
   *
   * @example
   * ```ts
   * const result = await apiClient.compareMultipleResumes({
   *   vacancy_id: 'vacancy-123',
   *   resume_ids: ['resume1', 'resume2', 'resume3'],
   * });
   * // Returns ranked comparison results with match percentages
   * ```
   */
  async compareMultipleResumes(request: CompareMultipleRequest): Promise<ComparisonMatrixData> {
    try {
      const response: AxiosResponse<ComparisonMatrixData> = await this.client.post(
        '/api/comparisons/compare-multiple',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Analytics ====================

  /**
   * Get key hiring metrics
   *
   * @param startDate - Optional start date for filtering (ISO 8601 format)
   * @param endDate - Optional end date for filtering (ISO 8601 format)
   * @returns Key metrics including time-to-hire, resume processing, and match rates
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const metrics = await apiClient.getKeyMetrics();
   * ```
   *
   * @example
   * ```ts
   * const metrics = await apiClient.getKeyMetrics('2024-01-01', '2024-12-31');
   * ```
   */
  async getKeyMetrics(
    startDate?: string,
    endDate?: string
  ): Promise<KeyMetricsResponse> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<KeyMetricsResponse> = await this.client.get(
        '/api/analytics/key-metrics',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get funnel visualization metrics
   *
   * @param startDate - Optional start date for filtering (ISO 8601 format)
   * @param endDate - Optional end date for filtering (ISO 8601 format)
   * @returns Funnel metrics showing candidate progression through pipeline
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const funnel = await apiClient.getFunnelMetrics();
   * ```
   *
   * @example
   * ```ts
   * const funnel = await apiClient.getFunnelMetrics('2024-01-01', '2024-12-31');
   * ```
   */
  async getFunnelMetrics(
    startDate?: string,
    endDate?: string
  ): Promise<FunnelMetricsResponse> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<FunnelMetricsResponse> = await this.client.get(
        '/api/analytics/funnel',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get skill demand analytics
   *
   * @param startDate - Optional start date for filtering (ISO 8601 format)
   * @param endDate - Optional end date for filtering (ISO 8601 format)
   * @param limit - Optional maximum number of skills to return (1-100, default 20)
   * @returns Skill demand data with trending skills
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const skills = await apiClient.getSkillDemand();
   * ```
   *
   * @example
   * ```ts
   * const skills = await apiClient.getSkillDemand('2024-01-01', '2024-12-31', 30);
   * ```
   */
  async getSkillDemand(
    startDate?: string,
    endDate?: string,
    limit?: number
  ): Promise<SkillDemandResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (limit !== undefined) params.limit = limit;

      const response: AxiosResponse<SkillDemandResponse> = await this.client.get(
        '/api/analytics/skill-demand',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get source tracking analytics
   *
   * @param startDate - Optional start date for filtering (ISO 8601 format)
   * @param endDate - Optional end date for filtering (ISO 8601 format)
   * @returns Source tracking data with vacancy distribution by source
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const sources = await apiClient.getSourceTracking();
   * ```
   *
   * @example
   * ```ts
   * const sources = await apiClient.getSourceTracking('2024-01-01', '2024-12-31');
   * ```
   */
  async getSourceTracking(
    startDate?: string,
    endDate?: string
  ): Promise<SourceTrackingResponse> {
    try {
      const params: Record<string, string> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response: AxiosResponse<SourceTrackingResponse> = await this.client.get(
        '/api/analytics/source-tracking',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get recruiter performance metrics
   *
   * @param startDate - Optional start date for filtering (ISO 8601 format)
   * @param endDate - Optional end date for filtering (ISO 8601 format)
   * @param limit - Optional maximum number of recruiters to return (1-100, default 20)
   * @returns Recruiter performance comparison data
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const recruiters = await apiClient.getRecruiterPerformance();
   * ```
   *
   * @example
   * ```ts
   * const recruiters = await apiClient.getRecruiterPerformance('2024-01-01', '2024-12-31', 10);
   * ```
   */
  async getRecruiterPerformance(
    startDate?: string,
    endDate?: string,
    limit?: number
  ): Promise<RecruiterPerformanceResponse> {
    try {
      const params: Record<string, string | number> = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (limit !== undefined) params.limit = limit;

      const response: AxiosResponse<RecruiterPerformanceResponse> = await this.client.get(
        '/api/analytics/recruiter-performance',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update language preference
   *
   * @param language - Language code to set as preference
   * @returns Language preference response
   */
  async updateLanguagePreference(language: string): Promise<LanguagePreferenceResponse> {
    try {
      const response: AxiosResponse<LanguagePreferenceResponse> = await this.client.post(
        '/api/preferences/language',
        { language }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }
}

// Extend AxiosRequestConfig to include metadata
declare module 'axios' {
  interface AxiosRequestConfig {
    metadata?: {
      startTime?: number;
      duration?: number;
    };
  }
}

/**
 * Default API client instance
 *
 * Use this singleton instance for all API calls.
 */
export const apiClient = new ApiClient();

/**
 * Export API client class for custom instances
 */
export default ApiClient;
