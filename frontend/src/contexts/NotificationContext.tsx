import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import {
  listNotifications,
  getUnreadCount,
  markAsRead,
  markAllAsRead,
  deleteNotification,
  getNotificationPreferences,
  updateNotificationPreferences,
} from '@/api/notifications';
import type {
  NotificationResponse,
  NotificationPreferences,
  NotificationPreferencesUpdate,
  UnreadCountResponse,
  ApiError,
} from '@/types/api';

/**
 * Notification context state interface
 */
interface NotificationState {
  /** List of notifications */
  notifications: NotificationResponse[];
  /** Total number of notifications */
  totalCount: number;
  /** Number of unread notifications */
  unreadCount: number;
  /** Unread count broken down by type */
  unreadCountByType: Record<string, number>;
  /** Unread count broken down by priority */
  unreadCountByPriority: Record<string, number>;
  /** Whether notifications are currently loading */
  isLoading: boolean;
  /** Whether there was an error loading notifications */
  error: string | null;
  /** WebSocket connection status */
  isWebSocketConnected: boolean;
  /** Notification preferences */
  preferences: NotificationPreferences | null;
  /** Whether preferences are loading */
  isLoadingPreferences: boolean;
}

/**
 * Notification context actions interface
 */
interface NotificationActions {
  /** Refresh notifications from server */
  refreshNotifications: () => Promise<void>;
  /** Mark a notification as read or unread */
  markNotificationRead: (notificationId: string, isRead: boolean) => Promise<void>;
  /** Mark all notifications as read */
  markAllRead: (type?: string) => Promise<void>;
  /** Delete a notification */
  deleteNotification: (notificationId: string) => Promise<void>;
  /** Refresh unread count */
  refreshUnreadCount: () => Promise<void>;
  /** Load notification preferences */
  loadPreferences: () => Promise<void>;
  /** Update notification preferences for a specific type */
  updatePreferences: (type: string, update: NotificationPreferencesUpdate) => Promise<void>;
  /** Clear error state */
  clearError: () => void;
}

/**
 * Combined notification context interface
 */
interface NotificationContextValue extends NotificationState, NotificationActions {}

/**
 * Notification provider props
 */
interface NotificationProviderProps {
  /** Children components */
  children: ReactNode;
  /** User ID for WebSocket connection and API requests */
  userId: string;
  /** Whether to auto-connect WebSocket (default: true) */
  autoConnect?: boolean;
  /** Polling interval for unread count fallback (ms, default: 60000) */
  pollingInterval?: number;
}

/**
 * Notification Context
 *
 * Provides global notification state and management for the application.
 * Integrates WebSocket for real-time updates and REST API for CRUD operations.
 *
 * @example
 * ```tsx
 * // Wrap your app with NotificationProvider
 * <NotificationProvider userId="user-123">
 *   <App />
 * </NotificationProvider>
 *
 * // Use in components
 * const { notifications, unreadCount, markNotificationRead } = useNotificationContext();
 *
 * // Display unread count
 * <Badge count={unreadCount} />
 *
 * // Mark notification as read
 * await markNotificationRead('notification-id', true);
 * ```
 */
const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

/**
 * Notification Provider Component
 *
 * Manages notification state, WebSocket connection for real-time updates,
 * and provides methods for notification CRUD operations.
 *
 * @param props - Provider props
 * @returns Notification context provider
 */
export const NotificationProvider: React.FC<NotificationProviderProps> = ({
  children,
  userId,
  autoConnect = true,
  pollingInterval = 60000,
}) => {
  // Notification state
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [unreadCountByType, setUnreadCountByType] = useState<Record<string, number>>({});
  const [unreadCountByPriority, setUnreadCountByPriority] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Preferences state
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [isLoadingPreferences, setIsLoadingPreferences] = useState(false);

  /**
   * Load notifications from server
   */
  const refreshNotifications = useCallback(async (): Promise<void> => {
    if (!userId) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await listNotifications();
      setNotifications(response.notifications);
      setTotalCount(response.total_count);
      setUnreadCount(response.unread_count);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load notifications');
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  /**
   * Load unread count from server
   */
  const refreshUnreadCount = useCallback(async (): Promise<void> => {
    if (!userId) {
      return;
    }

    try {
      const response: UnreadCountResponse = await getUnreadCount();
      setUnreadCount(response.count);
      setUnreadCountByType(response.by_type || {});
      setUnreadCountByPriority(response.by_priority || {});
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load unread count');
    }
  }, [userId]);

  /**
   * Mark notification as read or unread
   */
  const markNotificationRead = useCallback(
    async (notificationId: string, isRead: boolean): Promise<void> => {
      try {
        const response = await markAsRead(notificationId, isRead);

        // Update local state
        setNotifications((prev) =>
          prev.map((notification) =>
            notification.id === notificationId
              ? { ...notification, is_read: response.is_read, read_at: response.read_at }
              : notification
          )
        );

        // Update unread count
        if (isRead) {
          setUnreadCount((prev) => Math.max(0, prev - 1));
        } else {
          setUnreadCount((prev) => prev + 1);
        }
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to update notification');
        throw err;
      }
    },
    []
  );

  /**
   * Mark all notifications as read
   */
  const markAllRead = useCallback(
    async (type?: string): Promise<void> => {
      try {
        const response = await markAllAsRead(type);

        // Update local state
        setNotifications((prev) =>
          prev.map((notification) =>
            !type || notification.type === type
              ? { ...notification, is_read: true, read_at: new Date().toISOString() }
              : notification
          )
        );

        // Update unread count
        setUnreadCount((prev) => Math.max(0, prev - response.updated_count));
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to mark all as read');
        throw err;
      }
    },
    []
  );

  /**
   * Delete notification
   */
  const deleteNotification = useCallback(
    async (notificationId: string): Promise<void> => {
      try {
        await deleteNotification(notificationId);

        // Remove from local state
        setNotifications((prev) => {
          const notification = prev.find((n) => n.id === notificationId);
          const wasUnread = notification?.is_read === false;

          const filtered = prev.filter((n) => n.id !== notificationId);

          // Update counts
          setTotalCount(filtered.length);
          if (wasUnread) {
            setUnreadCount((count) => Math.max(0, count - 1));
          }

          return filtered;
        });
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to delete notification');
        throw err;
      }
    },
    []
  );

  /**
   * Load notification preferences
   */
  const loadPreferences = useCallback(async (): Promise<void> => {
    if (!userId) {
      return;
    }

    setIsLoadingPreferences(true);
    setError(null);

    try {
      const prefs = await getNotificationPreferences();
      setPreferences(prefs);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load preferences');
    } finally {
      setIsLoadingPreferences(false);
    }
  }, [userId]);

  /**
   * Update notification preferences
   */
  const updatePreferences = useCallback(
    async (type: string, update: NotificationPreferencesUpdate): Promise<void> => {
      try {
        const updatedPrefs = await updateNotificationPreferences(type, update);

        // Update local state
        if (preferences) {
          setPreferences({
            ...preferences,
            preferences: {
              ...preferences.preferences,
              [type]: updatedPrefs.settings,
            },
            updated_at: new Date().toISOString(),
          });
        }
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError.detail || 'Failed to update preferences');
        throw err;
      }
    },
    [preferences]
  );

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Handle incoming WebSocket notification
   */
  const handleWebSocketNotification = useCallback(
    (notification: NotificationResponse) => {
      // Add new notification to the beginning of the list
      setNotifications((prev) => {
        // Check if notification already exists (avoid duplicates)
        const exists = prev.some((n) => n.id === notification.id);
        if (exists) {
          return prev;
        }

        return [notification, ...prev];
      });

      // Update unread count if new notification is unread
      if (!notification.is_read) {
        setUnreadCount((prev) => prev + 1);
        setTotalCount((prev) => prev + 1);
      }
    },
    []
  );

  /**
   * Handle WebSocket connection state changes
   */
  const handleWebSocketConnect = useCallback(() => {
    // Clear any previous connection errors
    setError(null);
  }, []);

  const handleWebSocketError = useCallback((errorMsg: string) => {
    // Only set error for critical WebSocket issues
    // Don't show errors for temporary disconnections
    if (errorMsg.includes('Max reconnection attempts')) {
      setError(errorMsg);
    }
  }, []);

  // Setup WebSocket connection
  const { isConnected: isWebSocketConnected } = useWebSocket({
    userId,
    autoConnect,
    onNotification: handleWebSocketNotification,
    onConnect: handleWebSocketConnect,
    onError: handleWebSocketError,
  });

  /**
   * Load notifications on mount
   */
  useEffect(() => {
    if (userId) {
      refreshNotifications();
      refreshUnreadCount();
    }
  }, [userId, refreshNotifications, refreshUnreadCount]);

  /**
   * Setup polling for unread count as fallback
   * This runs even when WebSocket is connected to ensure data consistency
   */
  useEffect(() => {
    if (!userId) {
      return;
    }

    const interval = setInterval(() => {
      refreshUnreadCount();
    }, pollingInterval);

    return () => clearInterval(interval);
  }, [userId, pollingInterval, refreshUnreadCount]);

  const contextValue: NotificationContextValue = {
    notifications,
    totalCount,
    unreadCount,
    unreadCountByType,
    unreadCountByPriority,
    isLoading,
    error,
    isWebSocketConnected,
    preferences,
    isLoadingPreferences,
    refreshNotifications,
    markNotificationRead,
    markAllRead,
    deleteNotification,
    refreshUnreadCount,
    loadPreferences,
    updatePreferences,
    clearError,
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
    </NotificationContext.Provider>
  );
};

/**
 * useNotificationContext Hook
 *
 * Access notification context state and functions.
 * Must be used within a NotificationProvider.
 *
 * @throws Error if used outside of NotificationProvider
 * @returns Notification context state and actions
 *
 * @example
 * ```tsx
 * const { notifications, unreadCount, markNotificationRead } = useNotificationContext();
 *
 * // Display notifications
 * {notifications.map(notification => (
 *   <NotificationItem key={notification.id} notification={notification} />
 * ))}
 *
 * // Display unread count badge
 * <Badge count={unreadCount} />
 *
 * // Mark notification as read on click
 * const handleClick = async () => {
 *   await markNotificationRead(notification.id, true);
 * };
 * ```
 */
export const useNotificationContext = (): NotificationContextValue => {
  const context = useContext(NotificationContext);

  if (context === undefined) {
    throw new Error(
      'useNotificationContext must be used within a NotificationProvider. ' +
        'Wrap your component tree with <NotificationProvider userId="user-id">.'
    );
  }

  return context;
};

export default NotificationContext;
