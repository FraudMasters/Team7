/**
 * Audit Log API Service
 *
 * Provides methods for interacting with the audit logs endpoints.
 */
import axios, { AxiosInstance } from 'axios';
import { config } from '@/config';
import type {
  AuditLog,
  AuditLogsQuery,
  AuditLogsResponse,
  ActionTypesResponse,
  EntityTypesResponse,
} from '@/types/api';

class AuditLogApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: config.api.url,
      timeout: 30000, // 30 seconds for audit log queries
      headers: {
        'Content-Type': 'application/json',
      },
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
   * Get audit logs with filtering options
   */
  async getAuditLogs(params?: AuditLogsQuery): Promise<AuditLogsResponse> {
    const response = await this.client.get<AuditLogsResponse>('/api/audit-logs/', {
      params,
    });
    return response.data;
  }

  /**
   * Get available audit action types
   */
  async getActionTypes(): Promise<ActionTypesResponse> {
    const response = await this.client.get<ActionTypesResponse>(
      '/api/audit-logs/types'
    );
    return response.data;
  }

  /**
   * Get common entity types for filtering
   */
  async getEntityTypes(): Promise<EntityTypesResponse> {
    const response = await this.client.get<EntityTypesResponse>(
      '/api/audit-logs/entity-types'
    );
    return response.data;
  }
}

// Export singleton instance
export const auditLogApi = new AuditLogApiService();
export default auditLogApi;
