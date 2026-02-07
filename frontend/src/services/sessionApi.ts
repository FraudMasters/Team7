/**
 * Session API Service
 *
 * Provides methods for interacting with the session management endpoints.
 */
import axios, { AxiosInstance } from 'axios';
import type {
  SessionItem,
  SessionsListResponse,
  RevokeSessionResponse,
  RevokeAllSessionsResponse,
} from '@/types/api';

class SessionApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        throw error;
      }
    );
  }

  /**
   * Get user sessions with filtering options
   */
  async getSessions(params?: {
    user_id?: string;
    device_type?: 'desktop' | 'mobile' | 'tablet' | 'unknown';
    is_active?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<SessionsListResponse> {
    const response = await this.client.get<SessionsListResponse>('/api/sessions/', {
      params,
    });
    return response.data;
  }

  /**
   * Revoke a specific session
   */
  async revokeSession(sessionId: string, reason?: string): Promise<RevokeSessionResponse> {
    const response = await this.client.delete<RevokeSessionResponse>(
      `/api/sessions/${sessionId}`,
      { params: reason ? { reason } : undefined }
    );
    return response.data;
  }

  /**
   * Revoke all sessions for a user
   */
  async revokeAllSessions(params: {
    user_id: string;
    exclude_current?: boolean;
    reason?: string;
  }): Promise<RevokeAllSessionsResponse> {
    const response = await this.client.delete<RevokeAllSessionsResponse>(
      '/api/sessions/revoke-all',
      { params }
    );
    return response.data;
  }
}

// Export singleton instance
export const sessionApi = new SessionApiService();
export default sessionApi;
