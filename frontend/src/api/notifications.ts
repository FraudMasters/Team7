/**
 * Notifications API
 *
 * This module provides API functions for managing notifications and notification preferences,
 * including listing, creating, marking as read/unread, and updating preferences.
 *
 * @example
 * ```ts
 * import { listNotifications, getUnreadCount, markAsRead, updateNotificationPreferences } from '@/api/notifications';
 *
 * // Get all notifications
 * const notifications = await listNotifications();
 *
 * // Get unread count
 * const count = await getUnreadCount();
 * console.log(`Unread: ${count.count}`);
 *
 * // Mark notification as read
 * await markAsRead('notification-id', true);
 *
 * // Update preferences
 * await updateNotificationPreferences('new_match', {
 *   channels: { in_app: true, email: false, push: false, sms: false },
 *   digest_frequency: 'daily'
 * });
 * ```
 */

import { apiClient } from '@/api/client';
import type {
  NotificationResponse,
  NotificationListResponse,
  MarkNotificationReadRequest,
  MarkNotificationReadResponse,
  MarkAllReadRequest,
  MarkAllReadResponse,
  DeleteNotificationRequest,
  DeleteNotificationResponse,
  NotificationPreferences,
  NotificationPreferencesUpdate,
  NotificationPreferencesResponse,
  UnreadCountResponse,
  ApiError,
} from '@/types/api';

/**
 * List notifications with optional filters
 *
 * Retrieves notifications for the current user with optional filtering
 * by read status, type, priority, and date range.
 *
 * @param isRead - Optional filter by read status
 * @param type - Optional filter by notification type
 * @param priority - Optional filter by priority level
 * @param startDate - Optional start date for filtering (ISO 8601 format)
 * @param endDate - Optional end date for filtering (ISO 8601 format)
 * @returns Promise resolving to notification list response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * // Get all notifications
 * const all = await listNotifications();
 *
 * // Get only unread notifications
 * const unread = await listNotifications(false);
 *
 * // Get unread high-priority notifications
 * const urgent = await listNotifications(false, undefined, 'urgent');
 * ```
 */
export async function listNotifications(
  isRead?: boolean,
  type?: string,
  priority?: string,
  startDate?: string,
  endDate?: string
): Promise<NotificationListResponse> {
  try {
    const params: Record<string, string | boolean | undefined> = {};
    if (isRead !== undefined) params.is_read = isRead;
    if (type) params.type = type;
    if (priority) params.priority = priority;
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    const response = await apiClient.getAxiosInstance().get<NotificationListResponse>(
      '/api/notifications/',
      { params }
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve notifications'
    );
  }
}

/**
 * Get unread notification count
 *
 * Retrieves the count of unread notifications broken down by type and priority.
 *
 * @returns Promise resolving to unread count response
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const count = await getUnreadCount();
 * console.log(`Total unread: ${count.count}`);
 * console.log(`New matches: ${count.by_type?.new_match || 0}`);
 * console.log(`High priority: ${count.by_priority?.urgent || 0}`);
 * ```
 */
export async function getUnreadCount(): Promise<UnreadCountResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<UnreadCountResponse>(
      '/api/notifications/unread-count'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve unread count'
    );
  }
}

/**
 * Create a new notification
 *
 * Creates a new notification for a user. This is typically called by the backend
 * in response to events (e.g., candidate applied, stage changed).
 *
 * @param request - Notification data
 * @returns Promise resolving to created notification
 * @throws ApiError if creation fails
 *
 * @example
 * ```ts
 * const notification = await createNotification({
 *   user_id: 'user-123',
 *   type: 'new_match',
 *   priority: 'normal',
 *   title: 'New match found',
 *   message: 'A new candidate matches your vacancy',
 *   action_url: '/candidates/456',
 *   action_label: 'View Candidate'
 * });
 * ```
 */
export async function createNotification(
  request: Partial<NotificationResponse>
): Promise<NotificationResponse> {
  try {
    const response = await apiClient.getAxiosInstance().post<NotificationResponse>(
      '/api/notifications/',
      request
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to create notification'
    );
  }
}

/**
 * Mark a notification as read or unread
 *
 * Updates the read status of a specific notification.
 *
 * @param notificationId - Notification ID to update
 * @param isRead - Whether to mark as read (true) or unread (false)
 * @returns Promise resolving to updated notification
 * @throws ApiError if update fails
 *
 * @example
 * ```ts
 * // Mark as read
 * await markAsRead('notification-id', true);
 *
 * // Mark as unread
 * await markAsRead('notification-id', false);
 * ```
 */
export async function markAsRead(
  notificationId: string,
  isRead: boolean = true
): Promise<NotificationResponse> {
  try {
    const request: MarkNotificationReadRequest = { is_read: isRead };
    const response = await apiClient.getAxiosInstance().put<MarkNotificationReadResponse>(
      `/api/notifications/${notificationId}/mark-read`,
      request
    );
    return response.data.notification;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to update notification'
    );
  }
}

/**
 * Mark all notifications as read
 *
 * Marks all notifications (or all of a specific type) as read.
 *
 * @param type - Optional notification type filter
 * @returns Promise resolving to count of updated notifications
 * @throws ApiError if update fails
 *
 * @example
 * ```ts
 * // Mark all as read
 * const result = await markAllAsRead();
 * console.log(`Marked ${result.updated_count} as read`);
 *
 * // Mark all new_match notifications as read
 * const matches = await markAllAsRead('new_match');
 * ```
 */
export async function markAllAsRead(type?: string): Promise<MarkAllReadResponse> {
  try {
    const request: MarkAllReadRequest = type ? { filter_by_type: type } : {};
    const response = await apiClient.getAxiosInstance().put<MarkAllReadResponse>(
      '/api/notifications/mark-read',
      request
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to mark notifications as read'
    );
  }
}

/**
 * Delete a notification
 *
 * Permanently deletes a notification.
 *
 * @param notificationId - Notification ID to delete
 * @returns Promise resolving to deletion confirmation
 * @throws ApiError if deletion fails
 *
 * @example
 * ```ts
 * await deleteNotification('notification-id');
 * ```
 */
export async function deleteNotification(
  notificationId: string
): Promise<DeleteNotificationResponse> {
  try {
    const response = await apiClient.getAxiosInstance().delete<DeleteNotificationResponse>(
      `/api/notifications/${notificationId}`
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to delete notification'
    );
  }
}

/**
 * Get notification preferences
 *
 * Retrieves the current notification preferences for the user, including
 * channel settings and digest frequencies for each notification type.
 *
 * @returns Promise resolving to notification preferences
 * @throws ApiError if request fails
 *
 * @example
 * ```ts
 * const prefs = await getNotificationPreferences();
 * console.log('Email enabled:', prefs.preferences.new_match.channels.email);
 * ```
 */
export async function getNotificationPreferences(): Promise<NotificationPreferencesResponse> {
  try {
    const response = await apiClient.getAxiosInstance().get<NotificationPreferencesResponse>(
      '/api/notifications/preferences'
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to retrieve notification preferences'
    );
  }
}

/**
 * Update notification preferences
 *
 * Updates notification preferences for a specific notification type.
 * Allows configuring which channels to use and digest frequency.
 *
 * @param type - Notification type to update
 * @param update - Preference updates
 * @returns Promise resolving to updated preferences
 * @throws ApiError if update fails
 *
 * @example
 * ```ts
 * // Disable email for new_match notifications
 * const updated = await updateNotificationPreferences('new_match', {
 *   channels: {
 *     in_app: true,
 *     email: false,
 *     push: false,
 *     sms: false
 *   },
 *   digest_frequency: 'daily'
 * });
 *
 * // Enable quiet hours
 * await updateNotificationPreferences('candidate_applied', {
 *   quiet_hours: {
 *     enabled: true,
 *     start_time: '22:00',
 *     end_time: '08:00',
 *     timezone: 'America/New_York'
 *   }
 * });
 * ```
 */
export async function updateNotificationPreferences(
  type: string,
  update: NotificationPreferencesUpdate
): Promise<NotificationPreferencesResponse> {
  try {
    const response = await apiClient.getAxiosInstance().put<NotificationPreferencesResponse>(
      '/api/notifications/preferences',
      {
        notification_type: type,
        preferences: update,
      }
    );
    return response.data;
  } catch (error) {
    const apiError = error as ApiError;
    throw new Error(
      apiError.detail || 'Failed to update notification preferences'
    );
  }
}
