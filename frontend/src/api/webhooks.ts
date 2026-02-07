/**
 * Webhooks API Client
 *
 * Provides methods for managing webhook subscriptions and delivery logs.
 *
 * @module api/webhooks
 */

import { ApiClient } from './client';
import type { ApiError } from '@/types/api';

/**
 * Available webhook event types
 */
export enum WebhookEventType {
  // Candidate events
  CandidateCreated = 'candidate.created',
  CandidateUpdated = 'candidate.updated',
  CandidateDeleted = 'candidate.deleted',

  // Ranking events
  RankingCreated = 'ranking.created',
  RankingUpdated = 'ranking.updated',
  RankingDeleted = 'ranking.deleted',

  // Status change events
  StatusChanged = 'status.changed',
  StageChanged = 'stage.changed',

  // Resume events
  ResumeUploaded = 'resume.uploaded',
  ResumeProcessed = 'resume.processed',
  ResumeAnalyzed = 'resume.analyzed',

  // Vacancy events
  VacancyCreated = 'vacancy.created',
  VacancyUpdated = 'vacancy.updated',
  VacancyFilled = 'vacancy.filled',

  // Match events
  MatchCreated = 'match.created',
  MatchUpdated = 'match.updated',

  // Feedback events
  FeedbackSubmitted = 'feedback.submitted',

  // Report events
  ReportGenerated = 'report.generated',
  ReportExported = 'report.exported',

  // Note events
  NoteCreated = 'note.created',
  NoteUpdated = 'note.updated',

  // Workflow events
  WorkflowTriggered = 'workflow.triggered',
  WorkflowCompleted = 'workflow.completed',
  WorkflowFailed = 'workflow.failed',
}

/**
 * Webhook delivery status
 */
export enum WebhookDeliveryStatus {
  Pending = 'pending',
  Success = 'success',
  Failed = 'failed',
  Retrying = 'retrying',
}

/**
 * Webhook subscription data
 */
export interface WebhookSubscription {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  api_key_id: string | null;
  last_delivery_at: string | null;
  failure_count: number;
  created_at: string;
  updated_at: string;
}

/**
 * Webhook delivery log data
 */
export interface WebhookDeliveryLog {
  id: string;
  subscription_id: string;
  event_type: string;
  event_data: Record<string, unknown>;
  status: string;
  status_code: number | null;
  response_body: string | null;
  attempt_count: number;
  next_retry_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Webhook subscription with delivery logs
 */
export interface WebhookSubscriptionWithLogs extends WebhookSubscription {
  recent_deliveries: WebhookDeliveryLog[];
}

/**
 * Create webhook subscription request
 */
export interface CreateWebhookSubscriptionRequest {
  url: string;
  events: string[];
  secret?: string;
  api_key_id?: string;
}

/**
 * Create webhook subscription response
 */
export interface CreateWebhookSubscriptionResponse {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  api_key_id: string | null;
  last_delivery_at: string | null;
  failure_count: number;
  created_at: string;
  updated_at: string;
  message: string;
}

/**
 * Update webhook subscription request
 */
export interface UpdateWebhookSubscriptionRequest {
  url?: string;
  events?: string[];
  secret?: string;
}

/**
 * Update webhook subscription response
 */
export interface UpdateWebhookSubscriptionResponse {
  id: string;
  url: string;
  events: string[];
  is_active: boolean;
  api_key_id: string | null;
  last_delivery_at: string | null;
  failure_count: number;
  created_at: string;
  updated_at: string;
  message: string;
}

/**
 * Toggle webhook response
 */
export interface ToggleWebhookResponse {
  id: string;
  is_active: boolean;
  message: string;
}

/**
 * Webhook statistics
 */
export interface WebhookStatistics {
  total_subscriptions: number;
  active_subscriptions: number;
  total_deliveries_today: number;
  successful_deliveries_today: number;
  failed_deliveries_today: number;
}

/**
 * Webhooks Client
 *
 * Handles webhook subscription and delivery log management operations.
 */
export class WebhooksClient {
  /**
   * @param apiClient - The API client instance
   */
  constructor(private apiClient: ApiClient) {}

  /**
   * Create a new webhook subscription
   *
   * @param request - Webhook subscription details
   * @returns Created subscription details
   * @throws ApiError if creation fails
   *
   * @example
   * ```ts
   * const result = await webhooksClient.createSubscription({
   *   url: 'https://example.com/webhook',
   *   events: ['candidate.created', 'stage.changed'],
   *   secret: 'my-secret-key'
   * });
   * ```
   */
  async createSubscription(request: CreateWebhookSubscriptionRequest): Promise<CreateWebhookSubscriptionResponse> {
    try {
      const response = await this.apiClient.post<CreateWebhookSubscriptionResponse>(
        '/api/webhooks/subscribe',
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * List all webhook subscriptions
   *
   * @param isActive - Optional filter by active status
   * @param skip - Number of records to skip (default: 0)
   * @param limit - Maximum number of records to return (default: 100)
   * @returns List of webhook subscriptions
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const subscriptions = await webhooksClient.listSubscriptions();
   * const activeSubs = await webhooksClient.listSubscriptions(true);
   * ```
   */
  async listSubscriptions(
    isActive?: boolean,
    skip: number = 0,
    limit: number = 100
  ): Promise<WebhookSubscription[]> {
    try {
      const params: Record<string, number | boolean> = { skip, limit };
      if (isActive !== undefined) {
        params.is_active = isActive;
      }

      const response = await this.apiClient.getAxiosInstance().get<WebhookSubscription[]>(
        '/api/webhooks/',
        { params }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get a specific webhook subscription with delivery logs
   *
   * @param subscriptionId - Subscription UUID
   * @param skip - Number of delivery logs to skip (default: 0)
   * @param limit - Maximum number of delivery logs to return (default: 50)
   * @returns Subscription details with delivery logs
   * @throws ApiError if not found
   *
   * @example
   * ```ts
   * const subscription = await webhooksClient.getSubscription('sub-uuid');
   * ```
   */
  async getSubscription(
    subscriptionId: string,
    skip: number = 0,
    limit: number = 50
  ): Promise<WebhookSubscriptionWithLogs> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<WebhookSubscriptionWithLogs>(
        `/api/webhooks/${subscriptionId}`,
        { params: { skip, limit } }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Update a webhook subscription
   *
   * @param subscriptionId - Subscription UUID
   * @param request - Update details
   * @returns Updated subscription details
   * @throws ApiError if update fails
   *
   * @example
   * ```ts
   * const result = await webhooksClient.updateSubscription('sub-uuid', {
   *   url: 'https://example.com/new-webhook',
   *   events: ['candidate.created', 'stage.changed', 'ranking.created']
   * });
   * ```
   */
  async updateSubscription(
    subscriptionId: string,
    request: UpdateWebhookSubscriptionRequest
  ): Promise<UpdateWebhookSubscriptionResponse> {
    try {
      const response = await this.apiClient.put<UpdateWebhookSubscriptionResponse>(
        `/api/webhooks/${subscriptionId}`,
        request
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Delete a webhook subscription
   *
   * @param subscriptionId - Subscription UUID
   * @returns Success message
   * @throws ApiError if deletion fails
   *
   * @example
   * ```ts
   * await webhooksClient.deleteSubscription('sub-uuid');
   * ```
   */
  async deleteSubscription(subscriptionId: string): Promise<{ message: string }> {
    try {
      const response = await this.apiClient.delete<{ message: string }>(
        `/api/webhooks/${subscriptionId}`
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Enable a webhook subscription
   *
   * @param subscriptionId - Subscription UUID
   * @returns Toggle response
   * @throws ApiError if operation fails
   *
   * @example
   * ```ts
   * const result = await webhooksClient.enableSubscription('sub-uuid');
   * console.log(result.is_active); // true
   * ```
   */
  async enableSubscription(subscriptionId: string): Promise<ToggleWebhookResponse> {
    try {
      const response = await this.apiClient.post<ToggleWebhookResponse>(
        `/api/webhooks/${subscriptionId}/enable`,
        {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Disable a webhook subscription
   *
   * @param subscriptionId - Subscription UUID
   * @returns Toggle response
   * @throws ApiError if operation fails
   *
   * @example
   * ```ts
   * const result = await webhooksClient.disableSubscription('sub-uuid');
   * console.log(result.is_active); // false
   * ```
   */
  async disableSubscription(subscriptionId: string): Promise<ToggleWebhookResponse> {
    try {
      const response = await this.apiClient.post<ToggleWebhookResponse>(
        `/api/webhooks/${subscriptionId}/disable`,
        {}
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get delivery logs for a subscription
   *
   * @param subscriptionId - Subscription UUID
   * @param skip - Number of records to skip (default: 0)
   * @param limit - Maximum number of records to return (default: 50)
   * @returns List of delivery logs
   * @throws ApiError if listing fails
   *
   * @example
   * ```ts
   * const logs = await webhooksClient.getDeliveryLogs('sub-uuid');
   * ```
   */
  async getDeliveryLogs(
    subscriptionId: string,
    skip: number = 0,
    limit: number = 50
  ): Promise<WebhookDeliveryLog[]> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<WebhookDeliveryLog[]>(
        `/api/webhooks/${subscriptionId}/logs`,
        { params: { skip, limit } }
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Get webhook statistics
   *
   * @returns Webhook statistics
   * @throws ApiError if retrieval fails
   *
   * @example
   * ```ts
   * const stats = await webhooksClient.getStatistics();
   * console.log(stats.active_subscriptions);
   * ```
   */
  async getStatistics(): Promise<WebhookStatistics> {
    try {
      const response = await this.apiClient.getAxiosInstance().get<WebhookStatistics>(
        '/api/webhooks/statistics'
      );
      return response.data;
    } catch (error) {
      throw this.transformError(error);
    }
  }

  /**
   * Transform unknown error to ApiError
   */
  private transformError(error: unknown): ApiError {
    if (error && typeof error === 'object' && 'detail' in error) {
      const apiError = error as { detail: string; status?: number };
      return {
        detail: apiError.detail,
        status: apiError.status || 0,
      };
    }
    return {
      detail: error instanceof Error ? error.message : 'An unknown error occurred',
      status: 0,
    };
  }
}

/**
 * Default webhooks client instance
 */
export const webhooksClient = new WebhooksClient(
  new (require('./client').ApiClient)()
);

/**
 * Export webhooks client class
 */
export default WebhooksClient;
