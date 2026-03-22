/**
 * Audit Retention API Service
 *
 * Provides methods for interacting with audit log retention policy endpoints.
 */
import axios, { AxiosInstance } from 'axios';
import { config } from '@/config';

/**
 * Audit retention policy configuration
 */
export interface AuditRetentionConfig {
  retention_days: number;
  auto_cleanup_enabled: boolean;
  last_cleanup_at: string | null;
  total_logs: number;
  oldest_log_at: string | null;
}

/**
 * Audit retention policy update request
 */
export interface AuditRetentionConfigUpdate {
  retention_days: number;
}

class AuditRetentionApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: config.api.url,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('Audit Retention API error:', error);
        throw error;
      }
    );
  }

  /**
   * Get current audit retention configuration
   */
  async getRetentionConfig(): Promise<AuditRetentionConfig> {
    const response = await this.client.get<AuditRetentionConfig>('/api/audit/retention');
    return response.data;
  }

  /**
   * Update audit retention configuration
   */
  async updateRetentionConfig(config: AuditRetentionConfigUpdate): Promise<AuditRetentionConfig> {
    const response = await this.client.put<AuditRetentionConfig>('/api/audit/retention', config);
    return response.data;
  }
}

// Export singleton instance
export const auditRetentionApi = new AuditRetentionApiService();
export default auditRetentionApi;
