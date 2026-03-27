/**
 * Audit Alerts API Service
 *
 * Provides methods for interacting with audit alert configuration endpoints.
 */
import axios, { AxiosInstance } from 'axios';
import { config } from '@/config';

/**
 * Alert configuration item
 */
export interface AuditAlertConfig {
  id: string;
  name: string;
  alert_type: string;
  description: string | null;
  enabled: boolean;
  severity: string;
  organization_id: string | null;
  threshold: number;
  time_window_minutes: number;
  action_types: string[] | null;
  recipients: Record<string, unknown> | null;
  alert_config: Record<string, unknown> | null;
  cooldown_minutes: number;
  last_triggered_at: string | null;
  trigger_count: number;
  created_by: string | null;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Alert configurations list response
 */
export interface AuditAlertConfigsResponse {
  alert_configs: AuditAlertConfig[];
  total_count: number;
}

/**
 * Alert types response
 */
export interface AlertTypesResponse {
  alert_types: string[];
}

/**
 * Alert severities response
 */
export interface AlertSeveritiesResponse {
  severities: string[];
}

/**
 * Query parameters for fetching alert configurations
 */
export interface AuditAlertConfigsQuery {
  alert_type?: string;
  enabled?: boolean;
  severity?: string;
  organization_id?: string;
  limit?: number;
  offset?: number;
}

class AuditAlertsApiService {
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
        console.error('Audit Alerts API error:', error);
        throw error;
      }
    );
  }

  /**
   * Get audit alert configurations with filtering options
   */
  async getAlertConfigs(params?: AuditAlertConfigsQuery): Promise<AuditAlertConfigsResponse> {
    const response = await this.client.get<AuditAlertConfigsResponse>('/api/audit/alerts/', {
      params,
    });
    return response.data;
  }

  /**
   * Get available alert types
   */
  async getAlertTypes(): Promise<AlertTypesResponse> {
    const response = await this.client.get<AlertTypesResponse>('/api/audit/alerts/types');
    return response.data;
  }

  /**
   * Get available alert severity levels
   */
  async getAlertSeverities(): Promise<AlertSeveritiesResponse> {
    const response = await this.client.get<AlertSeveritiesResponse>('/api/audit/alerts/severities');
    return response.data;
  }
}

// Export singleton instance
export const auditAlertsApi = new AuditAlertsApiService();
export default auditAlertsApi;
