/**
 * Backup API Service
 *
 * Provides methods for interacting with the backup and restore endpoints.
 */
import axios, { AxiosInstance } from 'axios';
import type {
  Backup,
  BackupCreate,
  BackupRestoreRequest,
  BackupConfig,
  BackupConfigUpdate,
  BackupStatus,
  BackupVerifyResponse,
} from '@/types/api';

class BackupApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 300000, // 5 minutes for backup operations
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('Backup API error:', error);
        throw error;
      }
    );
  }

  /**
   * Get all backups
   */
  async getBackups(params?: {
    backup_type?: string;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<Backup[]> {
    const response = await this.client.get<Backup[]>('/api/backups/', { params });
    return response.data;
  }

  /**
   * Get backup status
   */
  async getBackupStatus(): Promise<BackupStatus> {
    const response = await this.client.get<BackupStatus>('/api/backups/status');
    return response.data;
  }

  /**
   * Get backup configuration
   */
  async getBackupConfig(): Promise<BackupConfig> {
    const response = await this.client.get<BackupConfig>('/api/backups/config');
    return response.data;
  }

  /**
   * Update backup configuration
   */
  async updateBackupConfig(config: BackupConfigUpdate): Promise<BackupConfig> {
    const response = await this.client.put<BackupConfig>('/api/backups/config', config);
    return response.data;
  }

  /**
   * Create a new backup
   */
  async createBackup(backup: BackupCreate): Promise<Backup> {
    const response = await this.client.post<Backup>('/api/backups/', backup);
    return response.data;
  }

  /**
   * Get a specific backup
   */
  async getBackup(backupId: string): Promise<Backup> {
    const response = await this.client.get<Backup>(`/api/backups/${backupId}`);
    return response.data;
  }

  /**
   * Restore from a backup
   */
  async restoreBackup(backupId: string, request: BackupRestoreRequest): Promise<{
    message: string;
    backup_id: string;
    task_id: string;
    restore_type: string;
  }> {
    const response = await this.client.post(`/api/backups/${backupId}/restore`, request);
    return response.data;
  }

  /**
   * Delete a backup
   */
  async deleteBackup(backupId: string): Promise<{ message: string }> {
    const response = await this.client.delete<{ message: string }>(`/api/backups/${backupId}`);
    return response.data;
  }

  /**
   * Verify backup integrity
   */
  async verifyBackup(backupId: string): Promise<BackupVerifyResponse> {
    const response = await this.client.post<BackupVerifyResponse>(`/api/backups/${backupId}/verify`);
    return response.data;
  }

  /**
   * Sync backups to S3
   */
  async syncS3(): Promise<{ message: string; task_id: string }> {
    const response = await this.client.post<{ message: string; task_id: string }>('/api/backups/sync-s3');
    return response.data;
  }

  /**
   * Cleanup old backups
   */
  async cleanupBackups(retentionDays?: number): Promise<{
    message: string;
    task_id: string;
    retention_days: number;
  }> {
    const response = await this.client.post<{
      message: string;
      task_id: string;
      retention_days: number;
    }>('/api/backups/cleanup', undefined, { params: { retention_days: retentionDays } });
    return response.data;
  }
}

// Export singleton instance
export const backupApi = new BackupApiService();
export default backupApi;
