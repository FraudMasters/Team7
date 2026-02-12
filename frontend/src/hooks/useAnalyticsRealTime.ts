/**
 * Analytics Real-Time Updates Hook
 *
 * This module provides a React hook for managing WebSocket connections
 * specifically for real-time analytics dashboard updates.
 *
 * @example
 * ```tsx
 * import { useAnalyticsRealTime } from '@/hooks/useAnalyticsRealTime';
 *
 * function AnalyticsDashboard() {
 *   const { isConnected, lastUpdate, refreshKey } = useAnalyticsRealTime({
 *     userId: 'user-123',
 *     onUpdate: (updateType, data) => {
 *       console.log(`Received ${updateType} update`);
 *     },
 *   });
 *
 *   // Use refreshKey to trigger data refresh in child components
 *   return (
 *     <div>
 *       <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
 *       <KeyMetrics refreshKey={refreshKey} />
 *     </div>
 *   );
 * }
 * ```
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type { AnalyticsUpdateType } from '@/types/api';

/**
 * Analytics real-time hook configuration options
 */
interface UseAnalyticsRealTimeOptions {
  /**
   * User ID for WebSocket connection
   * If not provided, will attempt to use stored user ID
   */
  userId?: string;

  /**
   * Callback when an analytics update is received
   * @param updateType - Type of analytics update (key_metrics, funnel, etc.)
   * @param data - The updated analytics data
   */
  onUpdate?: (updateType: AnalyticsUpdateType, data: Record<string, unknown>) => void;

  /**
   * Callback when connection is established
   */
  onConnect?: () => void;

  /**
   * Callback when connection is lost
   */
  onDisconnect?: () => void;

  /**
   * Callback when an error occurs
   * @param error - Error message
   */
  onError?: (error: string) => void;

  /**
   * Whether to automatically connect on mount
   * @default true
   */
  autoConnect?: boolean;

  /**
   * Whether to automatically reconnect on disconnect
   * @default true
   */
  autoReconnect?: boolean;

  /**
   * Maximum number of reconnection attempts
   * @default 5
   */
  maxReconnectAttempts?: number;

  /**
   * Delay between reconnection attempts (ms)
   * @default 3000
   */
  reconnectDelay?: number;

  /**
   * Interval for sending ping messages (ms)
   * @default 30000
   */
  pingInterval?: number;
}

/**
 * Analytics real-time hook return value
 */
interface UseAnalyticsRealTimeReturn {
  /**
   * Whether WebSocket is currently connected
   */
  isConnected: boolean;

  /**
   * Whether connection is currently being established
   */
  isConnecting: boolean;

  /**
   * Connection error message, if any
   */
  connectionError: string | null;

  /**
   * Number of reconnection attempts
   */
  reconnectAttempts: number;

  /**
   * Last received analytics update type
   */
  lastUpdate: AnalyticsUpdateType | null;

  /**
   * Timestamp of last update
   */
  lastUpdateTime: string | null;

  /**
   * Incrementing key that can be used to trigger re-renders in child components
   */
  refreshKey: number;

  /**
   * Manually connect to WebSocket
   */
  connect: () => void;

  /**
   * Manually disconnect from WebSocket
   */
  disconnect: () => void;

  /**
   * Force refresh trigger - increments refreshKey
   */
  triggerRefresh: () => void;
}

/**
 * Default configuration values
 */
const DEFAULT_CONFIG: Required<
  Omit<
    UseAnalyticsRealTimeOptions,
    'userId' | 'onUpdate' | 'onConnect' | 'onDisconnect' | 'onError'
  >
> = {
  autoConnect: true,
  autoReconnect: true,
  maxReconnectAttempts: 5,
  reconnectDelay: 3000,
  pingInterval: 30000,
};

/**
 * Get stored user ID from localStorage or session
 */
const getStoredUserId = (): string | null => {
  try {
    // Try to get user from localStorage auth data
    const authData = localStorage.getItem('auth');
    if (authData) {
      const parsed = JSON.parse(authData);
      if (parsed?.user?.id) {
        return parsed.user.id;
      }
    }

    // Fallback to sessionStorage
    const sessionAuth = sessionStorage.getItem('auth');
    if (sessionAuth) {
      const parsed = JSON.parse(sessionAuth);
      if (parsed?.user?.id) {
        return parsed.user.id;
      }
    }

    return null;
  } catch {
    return null;
  }
};

/**
 * Analytics real-time hook for dashboard updates
 *
 * Connects to the analytics WebSocket endpoint and provides real-time
 * updates for dashboard metrics. Uses refreshKey pattern to trigger
 * re-renders in child components when updates are received.
 *
 * @param options - Configuration options
 * @returns Connection state and refresh controls
 */
export const useAnalyticsRealTime = (
  options: UseAnalyticsRealTimeOptions = {}
): UseAnalyticsRealTimeReturn => {
  const {
    userId: providedUserId,
    onUpdate,
    onConnect,
    onDisconnect,
    onError,
    autoConnect = DEFAULT_CONFIG.autoConnect,
    autoReconnect = DEFAULT_CONFIG.autoReconnect,
    maxReconnectAttempts = DEFAULT_CONFIG.maxReconnectAttempts,
    reconnectDelay = DEFAULT_CONFIG.reconnectDelay,
    pingInterval = DEFAULT_CONFIG.pingInterval,
  } = options;

  // Get user ID from options or storage
  const userId = providedUserId || getStoredUserId();

  // WebSocket reference
  const wsRef = useRef<WebSocket | null>(null);

  // Reconnection timer reference
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Ping interval reference
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Update tracking
  const [lastUpdate, setLastUpdate] = useState<AnalyticsUpdateType | null>(null);
  const [lastUpdateTime, setLastUpdateTime] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  /**
   * Clear reconnection timeout
   */
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  /**
   * Clear ping interval
   */
  const clearPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  /**
   * Trigger a refresh - increment the refresh key
   */
  const triggerRefresh = useCallback(() => {
    setRefreshKey((prev) => prev + 1);
  }, []);

  /**
   * Build WebSocket URL
   */
  const buildWebSocketUrl = useCallback((): string | null => {
    if (!userId) {
      return null;
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_WS_URL || window.location.host;
    return `${protocol}//${host}/ws/notifications/${userId}`;
  }, [userId]);

  /**
   * Start ping interval to keep connection alive
   */
  const startPingInterval = useCallback(() => {
    clearPingInterval();

    pingIntervalRef.current = setInterval(() => {
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping', timestamp: new Date().toISOString() }));
      }
    }, pingInterval);
  }, [pingInterval, clearPingInterval]);

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data);

        // Handle different message types
        switch (message.type) {
          case 'analytics_update': {
            const updateType = message.update_type as AnalyticsUpdateType;
            const data = message.data as Record<string, unknown>;

            setLastUpdate(updateType);
            setLastUpdateTime(new Date().toISOString());

            // Trigger refresh
            triggerRefresh();

            // Call callback if provided
            if (onUpdate && updateType && data) {
              onUpdate(updateType, data);
            }
            break;
          }

          case 'notification': {
            // Check if this is an analytics-related notification
            const notificationData = message.notification || message.data;
            if (
              notificationData?.notification_type === 'analytics_update' ||
              notificationData?.notification_type === 'dashboard_refresh'
            ) {
              // Trigger refresh for analytics-related notifications
              triggerRefresh();
            }
            break;
          }

          case 'connection_established':
            // Server confirmed connection
            break;

          case 'pong':
            // Server responded to ping, connection is alive
            break;

          case 'error': {
            const errorMsg = message.error || message.message || 'Unknown WebSocket error';
            setConnectionError(errorMsg);
            if (onError) {
              onError(errorMsg);
            }
            break;
          }

          default:
            // Unknown message type - ignore
            break;
        }
      } catch (error) {
        const errorMsg = `Failed to parse WebSocket message: ${error instanceof Error ? error.message : 'Unknown error'}`;
        setConnectionError(errorMsg);
        if (onError) {
          onError(errorMsg);
        }
      }
    },
    [onUpdate, onError, triggerRefresh]
  );

  /**
   * Handle WebSocket connection open
   */
  const handleOpen = useCallback(() => {
    setIsConnected(true);
    setIsConnecting(false);
    setConnectionError(null);
    setReconnectAttempts(0);

    // Start ping interval
    startPingInterval();

    if (onConnect) {
      onConnect();
    }
  }, [onConnect, startPingInterval]);

  /**
   * Handle WebSocket connection close
   */
  const handleClose = useCallback(
    (event: CloseEvent) => {
      setIsConnected(false);
      setIsConnecting(false);
      clearPingInterval();

      if (onDisconnect) {
        onDisconnect();
      }

      // Attempt reconnection if enabled
      if (
        autoReconnect &&
        reconnectAttempts < maxReconnectAttempts &&
        event.code !== 1000 // Normal closure
      ) {
        reconnectTimeoutRef.current = setTimeout(() => {
          setReconnectAttempts((prev) => prev + 1);
          connect();
        }, reconnectDelay);
      } else if (reconnectAttempts >= maxReconnectAttempts) {
        setConnectionError(
          `Max reconnection attempts (${maxReconnectAttempts}) reached. Please refresh the page.`
        );
      }
    },
    [
      autoReconnect,
      reconnectAttempts,
      maxReconnectAttempts,
      reconnectDelay,
      onDisconnect,
      clearPingInterval,
    ]
  );

  /**
   * Handle WebSocket errors
   */
  const handleError = useCallback(() => {
    const errorMsg = 'WebSocket connection error';
    setConnectionError(errorMsg);
    setIsConnecting(false);

    if (onError) {
      onError(errorMsg);
    }
  }, [onError]);

  /**
   * Connect function reference for reconnection
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    if (!userId) {
      setConnectionError('No user ID available for WebSocket connection');
      return;
    }

    clearReconnectTimeout();
    setIsConnecting(true);
    setConnectionError(null);

    try {
      const wsUrl = buildWebSocketUrl();
      if (!wsUrl) {
        setConnectionError('Failed to build WebSocket URL');
        setIsConnecting(false);
        return;
      }

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.addEventListener('open', handleOpen);
      ws.addEventListener('message', handleMessage);
      ws.addEventListener('close', handleClose);
      ws.addEventListener('error', handleError);
    } catch (error) {
      const errorMsg = `Failed to create WebSocket connection: ${error instanceof Error ? error.message : 'Unknown error'}`;
      setConnectionError(errorMsg);
      setIsConnecting(false);

      if (onError) {
        onError(errorMsg);
      }
    }
  }, [
    userId,
    buildWebSocketUrl,
    handleOpen,
    handleMessage,
    handleClose,
    handleError,
    onError,
    clearReconnectTimeout,
  ]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    clearPingInterval();

    if (wsRef.current) {
      const ws = wsRef.current;
      ws.removeEventListener('open', handleOpen);
      ws.removeEventListener('message', handleMessage);
      ws.removeEventListener('close', handleClose);
      ws.removeEventListener('error', handleError);

      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close(1000, 'Client disconnect');
      }

      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
  }, [clearReconnectTimeout, clearPingInterval, handleOpen, handleMessage, handleClose, handleError]);

  /**
   * Setup connection on mount if autoConnect is enabled
   */
  useEffect(() => {
    if (autoConnect && userId) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  /**
   * Cleanup timers on unmount
   */
  useEffect(() => {
    return () => {
      clearReconnectTimeout();
      clearPingInterval();
    };
  }, [clearReconnectTimeout, clearPingInterval]);

  return {
    isConnected,
    isConnecting,
    connectionError,
    reconnectAttempts,
    lastUpdate,
    lastUpdateTime,
    refreshKey,
    connect,
    disconnect,
    triggerRefresh,
  };
};

export default useAnalyticsRealTime;
