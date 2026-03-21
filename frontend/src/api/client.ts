/**
 * API Client for Resume Analysis Backend
 *
 * This module provides a typed Axios client for communicating with the
 * backend resume analysis service. Handles resume upload, analysis,
 * job matching, and health check endpoints.
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
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { config } from '@/config';
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
  LanguagePreferenceUpdate,
  LanguagePreferenceResponse,
  ATSEvaluationRequest,
  ATSEvaluationResponse,
  BatchATSEvaluationRequest,
  BatchATSEvaluationResponse,
  ATSConfigResponse,
  ATSResultListResponse,
  WorkflowStageCreate,
  WorkflowStageUpdate,
  WorkflowStageResponse,
  WorkflowStageListResponse,
  CandidateListItem,
  MoveCandidateRequest,
  MoveCandidateResponse,
} from '@/types/api';

/**
 * Default API configuration
 *
 * Uses centralized configuration service for all values.
 */
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: config.api.url,
  timeout: config.api.timeout,
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

  /**
   * Generic POST request for custom endpoints
   *
   * @param url - Endpoint URL
   * @param data - Request payload
   * @returns Response data
   * @throws ApiError if request fails
   */
  async post<T = unknown>(url: string, data?: unknown): Promise<AxiosResponse<T>> {
    try {
      return await this.client.post<T>(url, data);
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

  // ==================== ATS Simulation ====================

  /**
   * Evaluate a resume against a job posting using ATS simulation
   *
   * @param request - ATS evaluation request with resume_id, vacancy_id, and optional use_llm flag
   * @returns Comprehensive ATS evaluation results
   * @throws ApiError if evaluation fails
   *
   * @example
   * ```ts
   * const result = await apiClient.evaluateATS({
   *   resume_id: 'resume-123',
   *   vacancy_id: 'vacancy-456',
   *   use_llm: true,
   * });
   * console.log(result.passed); // true/false
   * console.log(result.overall_score); // 0-1
   * console.log(result.missing_keywords); // ["Docker", "Kubernetes"]
   * ```
   */
  async evaluateATS(request: ATSEvaluationRequest): Promise<ATSEvaluationResponse> {
    try {
      const response: AxiosResponse<ATSEvaluationResponse> = await this.client.post(
        '/api/ats/evaluate',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get cached ATS evaluation result for a resume-vacancy pair
   *
   * @param resumeId - Resume ID
   * @param vacancyId - Job Vacancy ID
   * @returns Cached ATS evaluation result
   * @throws ApiError if result not found
   *
   * @example
   * ```ts
   * const result = await apiClient.getATSResult('resume-123', 'vacancy-456');
   * console.log(result.passed, result.overall_score);
   * ```
   */
  async getATSResult(resumeId: string, vacancyId: string): Promise<ATSEvaluationResponse> {
    try {
      const response: AxiosResponse<ATSEvaluationResponse> = await this.client.get(
        `/api/ats/results/${resumeId}/${vacancyId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Evaluate multiple resumes against a single job posting
   *
   * @param request - Batch evaluation request with vacancy_id and list of resume_ids
   * @returns Batch evaluation results with summary statistics
   * @throws ApiError if evaluation fails
   *
   * @example
   * ```ts
   * const result = await apiClient.batchEvaluateATS({
   *   vacancy_id: 'vacancy-456',
   *   resume_ids: ['resume-1', 'resume-2', 'resume-3'],
   *   use_llm: true,
   * });
   * console.log(`${result.passed_count}/${result.total_count} passed`);
   * ```
   */
  async batchEvaluateATS(request: BatchATSEvaluationRequest): Promise<BatchATSEvaluationResponse> {
    try {
      const response: AxiosResponse<BatchATSEvaluationResponse> = await this.client.post(
        '/api/ats/batch-evaluate',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get current ATS simulation configuration
   *
   * @returns ATS configuration including provider, model, threshold, and weights
   * @throws ApiError if request fails
   *
   * @example
   * ```ts
   * const config = await apiClient.getATSConfig();
   * console.log(config.llm_configured); // true/false
   * console.log(config.provider); // "openai"
   * console.log(config.threshold); // 0.6
   * ```
   */
  async getATSConfig(): Promise<ATSConfigResponse> {
    try {
      const response: AxiosResponse<ATSConfigResponse> = await this.client.get(
        '/api/ats/config'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List ATS results with optional filters
   *
   * @param resumeId - Optional resume ID filter
   * @param vacancyId - Optional vacancy ID filter
   * @param passed - Optional passed status filter
   * @param minScore - Optional minimum overall score filter
   * @param limit - Maximum number of results to return
   * @param offset - Number of results to skip
   * @returns List of ATS results with total count
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const results = await apiClient.listATSResults('vacancy-456');
   * console.log(`${results.total_count} results found`);
   * ```
   */
  async listATSResults(
    resumeId?: string,
    vacancyId?: string,
    passed?: boolean,
    minScore?: number,
    limit: number = 50,
    offset: number = 0
  ): Promise<ATSResultListResponse> {
    try {
      const params: Record<string, string | number | boolean> = {};
      if (resumeId) params.resume_id = resumeId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (passed !== undefined) params.passed = passed;
      if (minScore !== undefined) params.min_score = minScore;
      params.limit = limit;
      params.offset = offset;

      const response: AxiosResponse<ATSResultListResponse> = await this.client.get(
        '/api/ats/results',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Candidates ====================

  /**
   * List all candidates (resumes) with their current workflow stages
   *
   * @param stageId - Optional filter by workflow stage ID or name
   * @param vacancyId - Optional filter by vacancy ID
   * @param tagId - Optional filter by tag ID to show only candidates with this tag
   * @param skip - Number of records to skip (pagination)
   * @param limit - Maximum number of records to return
   * @returns List of candidates with their current stages
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all candidates
   * const candidates = await apiClient.listCandidates();
   *
   * // Filter by stage
   * const interviewCandidates = await apiClient.listCandidates('interview');
   *
   * // Filter by vacancy
   * const vacancyCandidates = await apiClient.listCandidates(undefined, 'vacancy-123');
   *
   * // Filter by tag
   * const taggedCandidates = await apiClient.listCandidates(undefined, undefined, 'tag-uuid');
   * ```
   */
  async listCandidates(
    stageId?: string,
    vacancyId?: string,
    tagId?: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<CandidateListItem[]> {
    try {
      const params: Record<string, string | number> = {};
      if (stageId) params.stage_id = stageId;
      if (vacancyId) params.vacancy_id = vacancyId;
      if (tagId) params.tag_id = tagId;
      params.skip = skip;
      params.limit = limit;

      const response: AxiosResponse<CandidateListItem[]> = await this.client.get(
        '/api/candidates/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific candidate's current stage information
   *
   * @param candidateId - Resume UUID
   * @returns Candidate details with current stage
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const candidate = await apiClient.getCandidate('resume-uuid');
   * console.log(candidate.current_stage, candidate.stage_name);
   * ```
   */
  async getCandidate(candidateId: string): Promise<CandidateListItem> {
    try {
      const response: AxiosResponse<CandidateListItem> = await this.client.get(
        `/api/candidates/${candidateId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Move a candidate to a different workflow stage
   *
   * Creates a new hiring stage record to track the stage transition.
   * This allows maintaining a complete history of candidate progression.
   *
   * @param candidateId - Resume UUID
   * @param request - Stage movement details (stage_id, optional vacancy_id, optional notes)
   * @returns New stage information
   * @throws ApiError if movement fails
   *
   * @example
   * ```ts
   * const result = await apiClient.moveCandidate('resume-uuid', {
   *   stage_id: 'interview',
   *   vacancy_id: 'vacancy-123',
   *   notes: 'Passed screening'
   * });
   * console.log(result.previous_stage, result.new_stage);
   * ```
   */
  async moveCandidate(
    candidateId: string,
    request: MoveCandidateRequest
  ): Promise<MoveCandidateResponse> {
    try {
      const response: AxiosResponse<MoveCandidateResponse> = await this.client.put(
        `/api/candidates/${candidateId}/stage`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  // ==================== Workflow Stages ====================

  /**
   * Create a workflow stage for an organization
   *
   * @param request - Create request with workflow stage details
   * @returns Created workflow stage
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const stage = await apiClient.createWorkflowStage({
   *   organization_id: 'org-123',
   *   stage_name: 'Technical Interview',
   *   stage_order: 3,
   *   is_active: true,
   *   color: '#3B82F6',
   *   description: 'Technical assessment with engineering team'
   * });
   * ```
   */
  async createWorkflowStage(request: WorkflowStageCreate): Promise<WorkflowStageResponse> {
    try {
      const response: AxiosResponse<WorkflowStageResponse> = await this.client.post(
        '/api/workflow-stages/',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List workflow stages with optional filters
   *
   * @param organizationId - Optional organization ID filter
   * @param isActive - Optional active status filter
   * @param isDefault - Optional default status filter
   * @returns List of workflow stages
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * // Get all stages for an organization
   * const stages = await apiClient.listWorkflowStages('org-123');
   *
   * // Get only active stages
   * const activeStages = await apiClient.listWorkflowStages('org-123', true);
   * ```
   */
  async listWorkflowStages(
    organizationId?: string,
    isActive?: boolean,
    isDefault?: boolean
  ): Promise<WorkflowStageListResponse> {
    try {
      const params: Record<string, string | boolean> = {};
      if (organizationId) params.organization_id = organizationId;
      if (isActive !== undefined) params.is_active = isActive;
      if (isDefault !== undefined) params.is_default = isDefault;

      const response: AxiosResponse<WorkflowStageListResponse> = await this.client.get(
        '/api/workflow-stages/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific workflow stage by ID
   *
   * @param stageId - Workflow stage ID
   * @returns Workflow stage details
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const stage = await apiClient.getWorkflowStage('stage-uuid');
   * ```
   */
  async getWorkflowStage(stageId: string): Promise<WorkflowStageResponse> {
    try {
      const response: AxiosResponse<WorkflowStageResponse> = await this.client.get(
        `/api/workflow-stages/${stageId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a workflow stage
   *
   * @param stageId - Workflow stage ID
   * @param request - Update request with fields to modify
   * @returns Updated workflow stage
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const updated = await apiClient.updateWorkflowStage('stage-uuid', {
   *   stage_name: 'Updated Technical Interview',
   *   is_active: false
   * });
   * ```
   */
  async updateWorkflowStage(
    stageId: string,
    request: WorkflowStageUpdate
  ): Promise<WorkflowStageResponse> {
    try {
      const response: AxiosResponse<WorkflowStageResponse> = await this.client.put(
        `/api/workflow-stages/${stageId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a workflow stage
   *
   * @param stageId - Workflow stage ID
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await apiClient.deleteWorkflowStage('stage-uuid');
   * ```
   */
  async deleteWorkflowStage(stageId: string): Promise<void> {
    try {
      await this.client.delete(`/api/workflow-stages/${stageId}`);
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
