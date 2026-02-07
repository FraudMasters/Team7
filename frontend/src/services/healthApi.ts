/**
 * Health Monitoring API Service
 *
 * Provides methods for interacting with the health check and system status endpoints.
 */
import axios, { AxiosInstance } from 'axios';
import type {
  SystemHealthResponse,
  LivenessResponse,
  ReadinessResponse,
} from '@/types/api';

class HealthApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 10000, // 10 seconds for health checks
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('Health API error:', error);
        throw error;
      }
    );
  }

  /**
   * Get comprehensive system health status
   */
  async getSystemHealth(): Promise<SystemHealthResponse> {
    const response = await this.client.get<SystemHealthResponse>('/api/health');
    return response.data;
  }

  /**
   * Check if the service is alive (liveness probe)
   */
  async getLiveness(): Promise<LivenessResponse> {
    const response = await this.client.get<LivenessResponse>('/api/health/live');
    return response.data;
  }

  /**
   * Check if the service is ready to handle requests (readiness probe)
   */
  async getReadiness(): Promise<ReadinessResponse> {
    const response = await this.client.get<ReadinessResponse>('/api/health/ready');
    return response.data;
  }
}

// Export singleton instance
export const healthApi = new HealthApiService();
export default healthApi;
