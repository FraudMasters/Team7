/**
 * Email Sync API Client
 *
 * This module provides a client for managing email synchronization with IMAP/SMTP servers,
 * including triggering manual syncs, checking sync status, and managing email configuration.
 *
 * @example
 * ```ts
 * import { emailSyncClient } from '@/api/emailSync';
 *
 * // Trigger email synchronization
 * const syncResult = await emailSyncClient.sync({
 *   full_sync: false,
 *   folder: 'INBOX'
 * });
 *
 * // Get sync status
 * const status = await emailSyncClient.getStatus();
 *
 * // Get email configuration
 * const config = await emailSyncClient.getConfig();
 *
 * // Update email configuration
 * const updated = await emailSyncClient.updateConfig({
 *   imap_enabled: true,
 *   imap_server: 'imap.gmail.com',
 *   imap_port: 993,
 *   imap_username: 'recruiting@example.com',
 *   imap_password: 'secure_password',
 *   sync_interval_minutes: 30
 * });
 * ```
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import type { ApiError } from '@/types/api';

/**
 * Email sync request
 */
export interface EmailSyncRequest {
  full_sync?: boolean;
  folder?: string;
}

/**
 * Email sync response
 */
export interface EmailSyncResponse {
  sync_id: string;
  status: string;
  message: string;
  emails_processed: number;
  emails_created: number;
  emails_updated: number;
  errors: string[];
}

/**
 * Email sync status response
 */
export interface EmailSyncStatusResponse {
  is_syncing: boolean;
  last_sync_time: string | null;
  last_sync_status: string;
  last_sync_duration_seconds: number | null;
  total_emails_synced: number;
  next_scheduled_sync: string | null;
  sync_config: Record<string, unknown>;
}

/**
 * Email configuration
 */
export interface EmailConfig {
  imap_enabled: boolean;
  imap_server: string;
  imap_port: number;
  imap_use_ssl: boolean;
  imap_username: string;
  smtp_enabled: boolean;
  smtp_server: string;
  smtp_port: number;
  smtp_use_ssl: boolean;
  smtp_username: string;
  sync_interval_minutes: number;
  sync_folders: string[];
  auto_link_candidates: boolean;
  sync_attachments: boolean;
}

/**
 * Email configuration update
 */
export interface EmailConfigUpdate {
  imap_enabled?: boolean;
  imap_server?: string;
  imap_port?: number;
  imap_use_ssl?: boolean;
  imap_username?: string;
  imap_password?: string;
  smtp_enabled?: boolean;
  smtp_server?: string;
  smtp_port?: number;
  smtp_use_ssl?: boolean;
  smtp_username?: string;
  smtp_password?: string;
  sync_interval_minutes?: number;
  sync_folders?: string[];
  auto_link_candidates?: boolean;
  sync_attachments?: boolean;
}

/**
 * Default API configuration for email sync client
 */
const DEFAULT_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL ?? '',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

/**
 * Email Sync API Client class
 *
 * Provides methods for managing email synchronization with proper
 * error handling and type safety.
 */
export class EmailSyncClient {
  private client: AxiosInstance;

  /**
   * Create a new EmailSync client instance
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
      409: 'A sync is already in progress.',
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
   * Trigger email synchronization
   *
   * @param request - Sync request with optional full_sync flag and folder specification
   * @returns Sync operation details including status and counts
   * @throws ApiError if sync fails to start
   *
   * @example
   * ```ts
   * // Trigger incremental sync for INBOX
   * const sync = await emailSyncClient.sync({
   *   full_sync: false,
   *   folder: 'INBOX'
   * });
   *
   * // Trigger full sync
   * const fullSync = await emailSyncClient.sync({
   *   full_sync: true
   * });
   * ```
   */
  async sync(request: EmailSyncRequest = {}): Promise<EmailSyncResponse> {
    try {
      const response: AxiosResponse<EmailSyncResponse> = await this.client.post(
        '/api/email-sync/sync',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get email synchronization status
   *
   * @returns Current sync status and configuration summary
   * @throws ApiError if status retrieval fails
   *
   * @example
   * ```ts
   * const status = await emailSyncClient.getStatus();
   * console.log(`Syncing: ${status.is_syncing}`);
   * console.log(`Last sync: ${status.last_sync_time}`);
   * console.log(`Total emails: ${status.total_emails_synced}`);
   * ```
   */
  async getStatus(): Promise<EmailSyncStatusResponse> {
    try {
      const response: AxiosResponse<EmailSyncStatusResponse> = await this.client.get(
        '/api/email-sync/status'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get email configuration
   *
   * Returns the current email configuration for IMAP/SMTP.
   * Sensitive information like passwords are never included in the response.
   *
   * @returns Current email configuration (excluding passwords)
   * @throws ApiError if config retrieval fails
   *
   * @example
   * ```ts
   * const config = await emailSyncClient.getConfig();
   * console.log(`IMAP enabled: ${config.imap_enabled}`);
   * console.log(`Sync interval: ${config.sync_interval_minutes} minutes`);
   * console.log(`Folders: ${config.sync_folders.join(', ')}`);
   * ```
   */
  async getConfig(): Promise<EmailConfig> {
    try {
      const response: AxiosResponse<EmailConfig> = await this.client.get(
        '/api/email-sync/config'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update email configuration
   *
   * Updates the email configuration for IMAP/SMTP synchronization.
   * Passwords can be updated but are never returned in the response.
   *
   * Only the fields specified in the request will be updated. All other fields
   * will remain unchanged. Partial updates are supported.
   *
   * @param request - Configuration update with only the fields to change
   * @returns Updated configuration (excluding passwords)
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * // Enable IMAP and configure server settings
   * const updated = await emailSyncClient.updateConfig({
   *   imap_enabled: true,
   *   imap_server: 'imap.gmail.com',
   *   imap_port: 993,
   *   imap_use_ssl: true,
   *   imap_username: 'recruiting@example.com',
   *   imap_password: 'secure_password',
   *   sync_interval_minutes: 30
   * });
   *
   * // Update just the sync interval
   * const intervalUpdate = await emailSyncClient.updateConfig({
   *   sync_interval_minutes: 60
   * });
   * ```
   */
  async updateConfig(request: EmailConfigUpdate): Promise<EmailConfig> {
    try {
      const response: AxiosResponse<EmailConfig> = await this.client.put(
        '/api/email-sync/config',
        request
      );
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
}

/**
 * Default email sync client instance
 *
 * Use this singleton instance for all email sync calls.
 */
export const emailSyncClient = new EmailSyncClient();

/**
 * Export email sync client class for custom instances
 */
export default EmailSyncClient;
