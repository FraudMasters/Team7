/**
 * WebSocket Hook for Real-Time Notifications
 *
 * This module provides a React hook for managing WebSocket connections
 * and handling real-time notification messages from the backend.
 *
 * @example
 * ```tsx
 * import { useWebSocket } from '@/hooks/useWebSocket';
 *
 * function NotificationListener() {
 *   const { isConnected, messages, connectionError } = useWebSocket({
 *     userId: 'user-123',
 *     onNotification: (notification) => {
 *       toast.info(`New: ${notification.title}`);
 *     },
 *     onError: (error) => {
 *       console.error('WebSocket error:', error);
 *     },
 *   });
 *
 *   return (
 *     <div>
 *       <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
 *       {connectionError && <p>Error: {connectionError}</p>}
 *     </div>
 *   );
 * }
 * ```
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type {
  WebSocketMessage,
  WebSocketNotificationMessage,
  WebSocketMessageType,
  WebSocketErrorMessage,
} from '@/types/api';

/**
 * WebSocket hook configuration options
 */
interface UseWebSocketOptions {
  /**
   * User ID for WebSocket connection path
   * Used to construct the WebSocket URL: /ws/notifications/{userId}
   */
  userId: string;

  /**
   * Callback when a notification is received
   * @param notification - The notification data
   */
  onNotification?: (notification: WebSocketNotificationMessage['notification']) => void;

  /**
   * Callback when any message is received
   * @param message - The raw message object
   */
  onMessage?: (message: WebSocketMessage) => void;

  /**
   * Callback when connection is established
   */
  onConnect?: () => void;

  /**
   * Callback when connection is closed
   * @param event - Close event with code and reason
   */
  onDisconnect?: (event: CloseEvent) => void;

  /**
   * Callback when an error occurs
   * @param error - Error message or details
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
   * @default 3000 (3 seconds)
   */
  reconnectDelay?: number;

  /**
   * Interval for sending ping messages (ms)
   * @default 30000 (30 seconds)
   */
  pingInterval?: number;
}

/**
 * WebSocket hook return value
 */
interface UseWebSocketReturn {
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
   * All received messages (for debugging or manual processing)
   */
  messages: WebSocketMessage[];

  /**
   * Manually connect to WebSocket
   */
  connect: () => void;

  /**
   * Manually disconnect from WebSocket
   */
  disconnect: () => void;

  /**
   * Send a message through the WebSocket
   * @param message - Message to send
   */
  sendMessage: (message: WebSocketMessage) => void;

  /**
   * Send acknowledgment for a received message
   * @param messageId - ID of the message to acknowledge
   */
  sendAck: (messageId: string) => void;
}

/**
 * Default configuration values
 */
const DEFAULT_CONFIG: Required<
  Omit<
    UseWebSocketOptions,
    'userId' | 'onNotification' | 'onMessage' | 'onConnect' | 'onDisconnect' | 'onError'
  >
> = {
  autoConnect: true,
  autoReconnect: true,
  maxReconnectAttempts: 5,
  reconnectDelay: 3000,
  pingInterval: 30000,
};

/**
 * WebSocket hook for managing real-time notification connections
 *
 * Provides automatic connection management, reconnection logic,
 * message handling, and connection status tracking.
 *
 * @param options - Configuration options for the WebSocket connection
 * @returns WebSocket connection state and control methods
 *
 * @example
 * ```tsx
 * const { isConnected, messages, connectionError } = useWebSocket({
 *   userId: 'user-123',
 *   onNotification: (notification) => {
 *     // Handle new notification
 *     showNotificationToast(notification);
 *   },
 *   onError: (error) => {
 *     // Handle error
 *     console.error('WebSocket error:', error);
 *   },
 * });
 * ```
 */
export const useWebSocket = (
  options: UseWebSocketOptions
): UseWebSocketReturn => {
  const {
    userId,
    onNotification,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    autoConnect = DEFAULT_CONFIG.autoConnect,
    autoReconnect = DEFAULT_CONFIG.autoReconnect,
    maxReconnectAttempts = DEFAULT_CONFIG.maxReconnectAttempts,
    reconnectDelay = DEFAULT_CONFIG.reconnectDelay,
    pingInterval = DEFAULT_CONFIG.pingInterval,
  } = options;

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
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);

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
   * Build WebSocket URL from user ID and environment
   */
  const buildWebSocketUrl = useCallback((): string => {
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
        const pingMessage: WebSocketMessage = {
          type: 'ping',
          id: `ping-${Date.now()}`,
          timestamp: new Date().toISOString(),
        };
        ws.send(JSON.stringify(pingMessage));
      }
    }, pingInterval);
  }, [pingInterval, clearPingInterval]);

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        // Add to messages list
        setMessages((prev) => [...prev, message]);

        // Call generic message handler
        if (onMessage) {
          onMessage(message);
        }

        // Handle specific message types
        switch (message.type) {
          case 'notification': {
            const notificationMessage = message as WebSocketNotificationMessage;
            if (onNotification) {
              onNotification(notificationMessage.notification);
            }

            // Send acknowledgment
            const ackMessage: WebSocketMessage = {
              type: 'notification_ack',
              id: `ack-${message.id}`,
              timestamp: new Date().toISOString(),
              original_message_id: message.id,
              status: 'received',
            };
            wsRef.current?.send(JSON.stringify(ackMessage));
            break;
          }

          case 'pong':
            // Server responded to ping, connection is alive
            break;

          case 'error': {
            const errorMessage = message as WebSocketErrorMessage;
            const errorMsg = errorMessage.error || 'Unknown WebSocket error';
            setConnectionError(errorMsg);
            if (onError) {
              onError(errorMsg);
            }
            break;
          }

          default:
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
    [onNotification, onMessage, onError]
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
        onDisconnect(event);
      }

      // Attempt reconnection if enabled and not explicitly closed by client
      if (
        autoReconnect &&
        reconnectAttempts < maxReconnectAttempts &&
        event.code !== 1000 // Normal closure
      ) {
        const errorMsg = `Connection closed: ${event.code} ${event.reason}`;
        setConnectionError(errorMsg);

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
  const handleError = useCallback(
    (event: Event) => {
      const errorMsg = 'WebSocket connection error';
      setConnectionError(errorMsg);
      setIsConnecting(false);

      if (onError) {
        onError(errorMsg);
      }
    },
    [onError]
  );

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    clearReconnectTimeout();
    setIsConnecting(true);
    setConnectionError(null);

    try {
      const wsUrl = buildWebSocketUrl();
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
  }, [userId, buildWebSocketUrl, handleOpen, handleMessage, handleClose, handleError, onError, clearReconnectTimeout]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    clearPingInterval();

    if (wsRef.current) {
      // Remove event listeners to prevent memory leaks
      const ws = wsRef.current;
      ws.removeEventListener('open', handleOpen);
      ws.removeEventListener('message', handleMessage);
      ws.removeEventListener('close', handleClose);
      ws.removeEventListener('error', handleError);

      // Close connection normally
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close(1000, 'Client disconnect');
      }

      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
  }, [clearReconnectTimeout, clearPingInterval, handleOpen, handleMessage, handleClose, handleError]);

  /**
   * Send a message through the WebSocket
   */
  const sendMessage = useCallback(
    (message: WebSocketMessage) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        throw new Error('WebSocket is not connected');
      }

      try {
        ws.send(JSON.stringify(message));
      } catch (error) {
        const errorMsg = `Failed to send message: ${error instanceof Error ? error.message : 'Unknown error'}`;
        setConnectionError(errorMsg);
        if (onError) {
          onError(errorMsg);
        }
        throw error;
      }
    },
    [onError]
  );

  /**
   * Send acknowledgment for a received message
   */
  const sendAck = useCallback(
    (messageId: string) => {
      const ackMessage: WebSocketMessage = {
        type: 'notification_ack',
        id: `ack-${messageId}-${Date.now()}`,
        timestamp: new Date().toISOString(),
        original_message_id: messageId,
        status: 'processed',
      };

      sendMessage(ackMessage);
    },
    [sendMessage]
  );

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
   * Cleanup timers and intervals on unmount
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
    messages,
    connect,
    disconnect,
    sendMessage,
    sendAck,
  };
};

export default useWebSocket;
