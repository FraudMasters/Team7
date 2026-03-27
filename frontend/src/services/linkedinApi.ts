/**
 * LinkedIn API Service
 *
 * Provides methods for interacting with the LinkedIn integration endpoints.
 * Supports profile search, candidate import, and outreach campaign management.
 */
import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';
import type {
  LinkedInAuthUrlResponse,
  LinkedInCallbackResponse,
  LinkedInSearchResponse,
  LinkedInSearchFilters,
  LinkedInProfileImportRequest,
  LinkedInProfileImportResponse,
  LinkedInCampaignResponse,
  LinkedInCampaignListResponse,
  LinkedInCampaignCreateRequest,
  LinkedInCampaignUpdateRequest,
  LinkedInCampaignStatsResponse,
  LinkedInOutreachResponse,
  LinkedInOutreachCreateRequest,
  LinkedInOutreachUpdateRequest,
} from '@/types/api';

/**
 * LinkedIn API Service class
 *
 * Provides methods for interacting with LinkedIn integration endpoints.
 * Includes comprehensive error handling and type safety.
 */
class LinkedInApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 30000, // 30 seconds for LinkedIn API operations
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('LinkedIn API error:', error);
        throw this.transformError(error);
      }
    );
  }

  /**
   * Transform Axios error to ApiError format
   */
  private transformError(error: unknown): ApiError {
    const axiosError = error as AxiosError<{ detail?: string }>;

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

    const status = axiosError.response.status;
    const data = axiosError.response.data;

    if (data?.detail) {
      return { detail: data.detail, status };
    }

    const defaultMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input.',
      401: 'Unauthorized. Please authenticate with LinkedIn.',
      403: 'Forbidden. You do not have permission to access this resource.',
      404: 'Resource not found.',
      409: 'A conflict occurred with this operation.',
      422: 'Validation error. Please check your input.',
      429: 'Too many requests. LinkedIn API rate limit reached. Please try again later.',
      500: 'Server error. Please try again later.',
      502: 'Bad gateway. Please try again later.',
      503: 'LinkedIn service unavailable. Please try again later.',
    };

    return {
      detail: defaultMessages[status] || 'An unexpected error occurred.',
      status,
    };
  }

  // ==================== Authentication Methods ====================

  /**
   * Get LinkedIn OAuth authentication URL
   *
   * @returns Promise with authentication URL and state parameter
   */
  async getAuthUrl(): Promise<LinkedInAuthUrlResponse> {
    const response: AxiosResponse<LinkedInAuthUrlResponse> = await this.client.get(
      '/api/linkedin/auth/url'
    );
    return response.data;
  }

  /**
   * Process LinkedIn OAuth callback
   *
   * @param code - Authorization code from LinkedIn
   * @param state - State parameter for CSRF protection
   * @returns Promise with callback response
   */
  async processCallback(code: string, state: string): Promise<LinkedInCallbackResponse> {
    const response: AxiosResponse<LinkedInCallbackResponse> = await this.client.get(
      '/api/linkedin/auth/callback',
      {
        params: { code, state },
      }
    );
    return response.data;
  }

  // ==================== Profile Search Methods ====================

  /**
   * Search LinkedIn profiles with filters
   *
   * @param filters - Search filters (keywords, location, skills, etc.)
   * @returns Promise with search results
   */
  async searchProfiles(filters?: LinkedInSearchFilters): Promise<LinkedInSearchResponse> {
    const params: Record<string, string | number> = {};

    if (filters?.keywords) params.keywords = filters.keywords;
    if (filters?.location) params.location = filters.location;
    if (filters?.skills) params.skills = filters.skills;
    if (filters?.title) params.title = filters.title;
    if (filters?.industry) params.industry = filters.industry;
    if (filters?.company) params.company = filters.company;
    if (filters?.experience_level) params.experience_level = filters.experience_level;
    if (filters?.limit !== undefined) params.limit = filters.limit;
    if (filters?.page !== undefined) params.page = filters.page;

    const response: AxiosResponse<LinkedInSearchResponse> = await this.client.get(
      '/api/linkedin/search',
      { params }
    );
    return response.data;
  }

  /**
   * Import a LinkedIn profile as a candidate
   *
   * @param request - Import request with profile URL and optional vacancy ID
   * @returns Promise with import response
   */
  async importProfile(request: LinkedInProfileImportRequest): Promise<LinkedInProfileImportResponse> {
    const response: AxiosResponse<LinkedInProfileImportResponse> = await this.client.post(
      '/api/linkedin/import',
      request
    );
    return response.data;
  }

  // ==================== Campaign Management Methods ====================

  /**
   * Get list of LinkedIn outreach campaigns
   *
   * @param vacancyId - Optional vacancy ID to filter campaigns
   * @returns Promise with campaign list
   */
  async getCampaigns(vacancyId?: string): Promise<LinkedInCampaignListResponse> {
    const params: Record<string, string> = {};
    if (vacancyId) params.vacancy_id = vacancyId;

    const response: AxiosResponse<LinkedInCampaignListResponse> = await this.client.get(
      '/api/linkedin/campaigns',
      { params }
    );
    return response.data;
  }

  /**
   * Get a single campaign by ID
   *
   * @param campaignId - Campaign UUID
   * @returns Promise with campaign details
   */
  async getCampaign(campaignId: string): Promise<LinkedInCampaignResponse> {
    const response: AxiosResponse<LinkedInCampaignResponse> = await this.client.get(
      `/api/linkedin/campaigns/${campaignId}`
    );
    return response.data;
  }

  /**
   * Create a new LinkedIn outreach campaign
   *
   * @param request - Campaign creation request
   * @returns Promise with created campaign
   */
  async createCampaign(request: LinkedInCampaignCreateRequest): Promise<LinkedInCampaignResponse> {
    const response: AxiosResponse<LinkedInCampaignResponse> = await this.client.post(
      '/api/linkedin/campaigns',
      request
    );
    return response.data;
  }

  /**
   * Update an existing campaign
   *
   * @param campaignId - Campaign UUID
   * @param request - Campaign update request
   * @returns Promise with updated campaign
   */
  async updateCampaign(
    campaignId: string,
    request: LinkedInCampaignUpdateRequest
  ): Promise<LinkedInCampaignResponse> {
    const response: AxiosResponse<LinkedInCampaignResponse> = await this.client.put(
      `/api/linkedin/campaigns/${campaignId}`,
      request
    );
    return response.data;
  }

  /**
   * Get campaign statistics
   *
   * @param campaignId - Campaign UUID
   * @returns Promise with campaign statistics
   */
  async getCampaignStats(campaignId: string): Promise<LinkedInCampaignStatsResponse> {
    const response: AxiosResponse<LinkedInCampaignStatsResponse> = await this.client.get(
      `/api/linkedin/campaigns/${campaignId}/stats`
    );
    return response.data;
  }

  // ==================== Outreach Management Methods ====================

  /**
   * Record a new outreach message in a campaign
   *
   * @param campaignId - Campaign UUID
   * @param request - Outreach creation request
   * @returns Promise with created outreach record
   */
  async createOutreach(
    campaignId: string,
    request: LinkedInOutreachCreateRequest
  ): Promise<LinkedInOutreachResponse> {
    const response: AxiosResponse<LinkedInOutreachResponse> = await this.client.post(
      `/api/linkedin/campaigns/${campaignId}/outreach`,
      request
    );
    return response.data;
  }

  /**
   * Update an outreach record (e.g., record a response)
   *
   * @param campaignId - Campaign UUID
   * @param outreachId - Outreach UUID
   * @param request - Outreach update request
   * @returns Promise with updated outreach record
   */
  async updateOutreach(
    campaignId: string,
    outreachId: string,
    request: LinkedInOutreachUpdateRequest
  ): Promise<LinkedInOutreachResponse> {
    const response: AxiosResponse<LinkedInOutreachResponse> = await this.client.put(
      `/api/linkedin/campaigns/${campaignId}/outreach/${outreachId}`,
      request
    );
    return response.data;
  }

  /**
   * Get list of outreach messages for a campaign
   *
   * @param campaignId - Campaign UUID
   * @returns Promise with outreach message list
   */
  async getOutreachList(campaignId: string): Promise<LinkedInOutreachResponse[]> {
    const response: AxiosResponse<LinkedInOutreachResponse[]> = await this.client.get(
      `/api/linkedin/campaigns/${campaignId}/outreach`
    );
    return response.data;
  }
}

// Export singleton instance
export const linkedinApi = new LinkedInApiService();
export default linkedinApi;
