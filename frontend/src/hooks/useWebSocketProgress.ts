/**
 * WebSocket Progress Hook for Real-Time Batch Updates
 *
 * This module provides a React hook for managing WebSocket connections
 * specifically for real-time resume processing progress updates during
 * batch operations.
 *
 * @example
 * ```tsx
 * import { useWebSocketProgress } from '@/hooks/useWebSocketProgress';
 *
 * function BatchUploadProgress({ batchId }: { batchId: string }) {
 *   const {
 *     isConnected,
 *     batchState,
 *     resumeStates,
 *     connectionError,
 *   } = useWebSocketProgress({
 *     batchId,
 *     onProgressUpdate: (update) => {
 *       console.log(`Progress: ${update.progress}%`);
 *     },
 *     onComplete: (resumeId, state) => {
 *       console.log(`Resume ${resumeId} completed`);
 *     },
 *     onError: (resumeId, error) => {
 *       console.error(`Resume ${resumeId} failed:`, error);
 *     },
 *   });
 *
 *   return (
 *     <div>
 *       <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
 *       {batchState && (
 *         <p>Progress: {batchState.progress}% ({batchState.completed_count}/{batchState.total_resumes})</p>
 *       )}
 *     </div>
 *   );
 * }
 * ```
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import type {
  ResumeProgressUpdate,
  BatchProgressUpdate,
  ResumeProgressError,
  ResumeProgressStage,
  ResumeProcessingState,
  BatchProcessingState,
  ProgressUpdateCallback,
  BatchProgressUpdateCallback,
  ProcessingCompleteCallback,
  ProcessingErrorCallback,
} from '@/types/resume-progress';

/**
 * WebSocket progress hook configuration options
 */
interface UseWebSocketProgressOptions {
  /**
   * Batch ID for WebSocket connection path
   * Used to construct the WebSocket URL: /ws/resume_progress/{batchId}
   */
  batchId: string;

  /**
   * Callback when an individual resume progress update is received
   * @param update - The progress update data
   */
  onProgressUpdate?: ProgressUpdateCallback;

  /**
   * Callback when a batch progress update is received
   * @param update - The batch progress update data
   */
  onBatchProgress?: BatchProgressUpdateCallback;

  /**
   * Callback when a resume finishes processing (success or failure)
   * @param resumeId - The resume ID
   * @param state - The final processing state
   */
  onComplete?: ProcessingCompleteCallback;

  /**
   * Callback when a resume processing error occurs
   * @param resumeId - The resume ID
   * @param error - The error details
   */
  onError?: ProcessingErrorCallback;

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
   * Callback when a connection error occurs
   * @param error - Error message or details
   */
  onConnectionError?: (error: string) => void;

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
   * @default 10
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
 * WebSocket progress hook return value
 */
interface UseWebSocketProgressReturn {
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
   * Current batch processing state
   */
  batchState: BatchProcessingState | null;

  /**
   * Individual resume processing states indexed by resume_id
   */
  resumeStates: Record<string, ResumeProcessingState>;

  /**
   * All received progress messages for debugging
   */
  messages: Array<ResumeProgressUpdate | BatchProgressUpdate>;

  /**
   * Manually connect to WebSocket
   */
  connect: () => void;

  /**
   * Manually disconnect from WebSocket
   */
  disconnect: () => void;

  /**
   * Reset the progress state
   */
  resetState: () => void;
}

/**
 * Default configuration values
 */
const DEFAULT_CONFIG: Required<
  Omit<
    UseWebSocketProgressOptions,
    | 'batchId'
    | 'onProgressUpdate'
    | 'onBatchProgress'
    | 'onComplete'
    | 'onError'
    | 'onConnect'
    | 'onDisconnect'
    | 'onConnectionError'
  >
> = {
  autoConnect: true,
  autoReconnect: true,
  maxReconnectAttempts: 10,
  reconnectDelay: 3000,
  pingInterval: 30000,
};

/**
 * Create initial batch processing state
 */
const createInitialBatchState = (batchId: string): BatchProcessingState => ({
  task_id: batchId,
  total_resumes: 0,
  processing_count: 0,
  completed_count: 0,
  failed_count: 0,
  progress: 0,
  resumes: {},
  completed_resume_ids: [],
  failed_resume_ids: [],
  is_complete: false,
  has_errors: false,
  started_at: new Date(),
});

/**
 * Create initial resume processing state
 */
const createInitialResumeState = (resumeId: string): ResumeProcessingState => ({
  resume_id: resumeId,
  stage: 'parsing' as ResumeProgressStage,
  progress: 0,
  message: '',
  is_complete: false,
  has_error: false,
  started_at: new Date(),
});

/**
 * WebSocket progress hook for real-time batch processing updates
 *
 * Provides automatic connection management, reconnection logic,
 * progress state tracking, and connection status monitoring.
 *
 * @param options - Configuration options for the WebSocket connection
 * @returns WebSocket connection state, progress state, and control methods
 */
export const useWebSocketProgress = (
  options: UseWebSocketProgressOptions
): UseWebSocketProgressReturn => {
  const {
    batchId,
    onProgressUpdate,
    onBatchProgress,
    onComplete,
    onError,
    onConnect,
    onDisconnect,
    onConnectionError,
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

  // Progress state
  const [batchState, setBatchState] = useState<BatchProcessingState | null>(null);
  const [resumeStates, setResumeStates] = useState<Record<string, ResumeProcessingState>>({});
  const [messages, setMessages] = useState<Array<ResumeProgressUpdate | BatchProgressUpdate>>([]);

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
   * Reset progress state
   */
  const resetState = useCallback(() => {
    setBatchState(null);
    setResumeStates({});
    setMessages([]);
  }, []);

  /**
   * Build WebSocket URL from batch ID and environment
   */
  const buildWebSocketUrl = useCallback((): string => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_WS_URL || window.location.host;
    return `${protocol}//${host}/ws/resume_progress/${batchId}`;
  }, [batchId]);

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
   * Update resume state from progress update
   */
  const updateResumeState = useCallback(
    (update: ResumeProgressUpdate) => {
      const { resume_id, stage, progress, message, metadata } = update;

      setResumeStates((prev) => {
        const existingState = prev[resume_id];
        const newState: ResumeProcessingState = {
          resume_id,
          stage,
          progress,
          message,
          is_complete: stage === 'complete',
          has_error: stage === 'failed',
          error: stage === 'failed' ? (update as ResumeProgressError).error_message : undefined,
          started_at: existingState?.started_at || new Date(),
          completed_at: stage === 'complete' || stage === 'failed' ? new Date() : undefined,
          metadata,
        };

        return {
          ...prev,
          [resume_id]: newState,
        };
      });

      // Handle completion callbacks
      if (stage === 'complete') {
        const state: ResumeProcessingState = {
          resume_id,
          stage,
          progress,
          message,
          is_complete: true,
          has_error: false,
          started_at: new Date(),
          completed_at: new Date(),
          metadata,
        };
        onComplete?.(resume_id, state);
      }

      if (stage === 'failed') {
        const errorUpdate = update as ResumeProgressError;
        onError?.(resume_id, errorUpdate);
      }
    },
    [onComplete, onError]
  );

  /**
   * Update batch state from batch progress update
   */
  const updateBatchState = useCallback(
    (update: BatchProgressUpdate) => {
      const {
        task_id,
        current,
        total,
        progress,
        message,
        completed_resumes,
        failed_resumes,
      } = update;

      setBatchState((prev) => {
        const currentState = prev || createInitialBatchState(task_id);
        const newState: BatchProcessingState = {
          ...currentState,
          task_id,
          total_resumes: total,
          progress,
          completed_count: completed_resumes?.length || current,
          failed_count: failed_resumes?.length || currentState.failed_count,
          completed_resume_ids: completed_resumes || currentState.completed_resume_ids,
          failed_resume_ids: failed_resumes || currentState.failed_resume_ids,
          is_complete: progress >= 100,
          has_errors: (failed_resumes?.length || 0) > 0,
        };

        return newState;
      });
    },
    []
  );

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        // Add to messages list for debugging
        setMessages((prev) => [...prev.slice(-99), data]); // Keep last 100 messages

        // Handle specific message types
        switch (data.type) {
          case 'resume_progress': {
            const progressMessage = data as ResumeProgressUpdate;
            updateResumeState(progressMessage);
            onProgressUpdate?.(progressMessage);
            break;
          }

          case 'batch_progress': {
            const batchMessage = data as BatchProgressUpdate;
            updateBatchState(batchMessage);
            onBatchProgress?.(batchMessage);
            break;
          }

          case 'connection_established':
            // Server confirmed connection
            break;

          case 'pong':
            // Server responded to ping, connection is alive
            break;

          case 'error': {
            const errorMsg = data.error || data.message || 'Unknown WebSocket error';
            setConnectionError(errorMsg);
            onConnectionError?.(errorMsg);
            break;
          }

          default:
            // Unknown message type - ignore or log for debugging
            break;
        }
      } catch (error) {
        const errorMsg = `Failed to parse WebSocket message: ${error instanceof Error ? error.message : 'Unknown error'}`;
        setConnectionError(errorMsg);
        onConnectionError?.(errorMsg);
      }
    },
    [updateResumeState, updateBatchState, onProgressUpdate, onBatchProgress, onConnectionError]
  );

  /**
   * Handle WebSocket connection open
   */
  const handleOpen = useCallback(() => {
    setIsConnected(true);
    setIsConnecting(false);
    setConnectionError(null);
    setReconnectAttempts(0);

    // Initialize batch state if not exists
    setBatchState((prev) => prev || createInitialBatchState(batchId));

    // Start ping interval
    startPingInterval();

    if (onConnect) {
      onConnect();
    }
  }, [batchId, onConnect, startPingInterval]);

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
        const maxError = `Max reconnection attempts (${maxReconnectAttempts}) reached. Please refresh the page.`;
        setConnectionError(maxError);
        onConnectionError?.(maxError);
      }
    },
    [
      autoReconnect,
      reconnectAttempts,
      maxReconnectAttempts,
      reconnectDelay,
      onDisconnect,
      onConnectionError,
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

      if (onConnectionError) {
        onConnectionError(errorMsg);
      }
    },
    [onConnectionError]
  );

  /**
   * Connect function reference for reconnection
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

      if (onConnectionError) {
        onConnectionError(errorMsg);
      }
    }
  }, [
    batchId,
    buildWebSocketUrl,
    handleOpen,
    handleMessage,
    handleClose,
    handleError,
    onConnectionError,
    clearReconnectTimeout,
  ]);

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
   * Setup connection on mount if autoConnect is enabled
   */
  useEffect(() => {
    if (autoConnect && batchId) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [batchId]);

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
    batchState,
    resumeStates,
    messages,
    connect,
    disconnect,
    resetState,
  };
};

export default useWebSocketProgress;
