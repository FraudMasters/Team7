/**
 * Resume processing progress type definitions
 *
 * This module contains TypeScript interfaces for real-time resume processing
 * progress updates via WebSocket. These types enable the frontend to track
 * and display progress during resume parsing, analysis, and ranking stages.
 *
 * The types align with the backend progress stages defined in
 * backend/websocket/resume_progress.py.
 */

/**
 * Resume processing stages
 *
 * Represents the sequential stages of resume processing pipeline.
 * Each stage corresponds to a specific phase of analysis.
 */
export type ResumeProgressStage =
  | 'parsing'     // Extracting text and metadata from resume file
  | 'analyzing'   // Running ML/NLP analysis (keywords, entities, grammar, etc.)
  | 'ranking'     // Calculating match scores and rankings
  | 'complete'    // Processing finished successfully
  | 'failed';     // Processing encountered an error

/**
 * Base WebSocket message structure for resume progress
 */
export interface ResumeProgressMessageBase {
  /** Message type identifier */
  type: string;
  /** ISO format timestamp of message creation */
  timestamp: string;
  /** Unique identifier for the processing task (Celery task ID) */
  task_id: string;
  /** Current processing stage */
  stage: ResumeProgressStage;
  /** Current progress percentage (0-100) */
  progress: number;
  /** Human-readable progress message */
  message: string;
}

/**
 * Single resume progress update message
 *
 * Sent when processing a single resume through the pipeline.
 */
export interface ResumeProgressUpdate extends ResumeProgressMessageBase {
  type: 'resume_progress';
  /** Resume identifier */
  resume_id: string;
  /** Optional additional context data */
  metadata?: Record<string, unknown>;
}

/**
 * Batch processing progress update message
 *
 * Sent during batch resume processing operations.
 */
export interface BatchProgressUpdate extends ResumeProgressMessageBase {
  type: 'batch_progress';
  /** Current number of processed resumes */
  current: number;
  /** Total number of resumes to process */
  total: number;
  /** List of completed resume IDs (in metadata) */
  completed_resumes?: string[];
  /** List of failed resume IDs (in metadata) */
  failed_resumes?: string[];
}

/**
 * Completion message for resume processing
 *
 * Sent when a resume processing task completes successfully.
 */
export interface ResumeProgressComplete extends ResumeProgressMessageBase {
  type: 'resume_progress';
  /** Resume identifier */
  resume_id: string;
  stage: 'complete';
  progress: 100;
  /** Optional result data (e.g., analysis scores, keywords) */
  metadata?: {
    score?: number;
    keywords?: string[];
    processing_time_ms?: number;
    [key: string]: unknown;
  };
}

/**
 * Error message for failed resume processing
 *
 * Sent when a resume processing task fails.
 */
export interface ResumeProgressError extends ResumeProgressMessageBase {
  type: 'resume_progress';
  /** Resume identifier */
  resume_id: string;
  stage: 'failed';
  /** Human-readable error description */
  error_message: string;
  /** Optional error context data */
  metadata?: {
    error_type?: string;
    error_details?: string;
    retry_available?: boolean;
    [key: string]: unknown;
  };
}

/**
 * Union type for all resume progress message types
 */
export type ResumeProgressMessage =
  | ResumeProgressUpdate
  | BatchProgressUpdate
  | ResumeProgressComplete
  | ResumeProgressError;

/**
 * Progress state for a single resume being processed
 */
export interface ResumeProcessingState {
  /** Resume identifier */
  resume_id: string;
  /** Current processing stage */
  stage: ResumeProgressStage;
  /** Progress percentage (0-100) */
  progress: number;
  /** Current status message */
  message: string;
  /** Whether processing has completed */
  is_complete: boolean;
  /** Whether processing has failed */
  has_error: boolean;
  /** Error message if processing failed */
  error?: string;
  /** Processing start time */
  started_at: Date;
  /** Processing end time (if complete) */
  completed_at?: Date;
  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Batch processing state
 *
 * Tracks progress for multiple resumes being processed in parallel.
 */
export interface BatchProcessingState {
  /** Unique identifier for the batch task */
  task_id: string;
  /** Total number of resumes in batch */
  total_resumes: number;
  /** Number of resumes currently being processed */
  processing_count: number;
  /** Number of resumes that completed successfully */
  completed_count: number;
  /** Number of resumes that failed */
  failed_count: number;
  /** Overall batch progress percentage (0-100) */
  progress: number;
  /** Individual resume states indexed by resume_id */
  resumes: Record<string, ResumeProcessingState>;
  /** List of completed resume IDs */
  completed_resume_ids: string[];
  /** List of failed resume IDs */
  failed_resume_ids: string[];
  /** Whether the entire batch is complete */
  is_complete: boolean;
  /** Whether the batch was stopped due to errors */
  has_errors: boolean;
  /** Batch start time */
  started_at: Date;
  /** Batch completion time (if complete) */
  completed_at?: Date;
}

/**
 * Initial state factory for a single resume processing
 */
export interface CreateResumeProcessingStateParams {
  resume_id: string;
  started_at?: Date;
}

/**
 * Progress update callback type
 *
 * Called when a progress update is received for a resume.
 */
export type ProgressUpdateCallback = (update: ResumeProgressUpdate) => void;

/**
 * Batch progress update callback type
 *
 * Called when a batch progress update is received.
 */
export type BatchProgressUpdateCallback = (update: BatchProgressUpdate) => void;

/**
 * Completion callback type
 *
 * Called when a resume finishes processing (success or failure).
 */
export type ProcessingCompleteCallback = (
  resume_id: string,
  state: ResumeProcessingState
) => void;

/**
 * Error callback type
 *
 * Called when a resume processing error occurs.
 */
export type ProcessingErrorCallback = (
  resume_id: string,
  error: ResumeProgressError
) => void;

/**
 * Configuration options for resume progress tracking
 */
export interface ResumeProgressOptions {
  /** Callback for individual progress updates */
  onProgressUpdate?: ProgressUpdateCallback;
  /** Callback for batch progress updates */
  onBatchProgress?: BatchProgressUpdateCallback;
  /** Callback when processing completes successfully */
  onComplete?: ProcessingCompleteCallback;
  /** Callback when processing encounters an error */
  onError?: ProcessingErrorCallback;
  /** Whether to show detailed progress messages */
  verbose?: boolean;
  /** Timeout for processing in milliseconds (0 = no timeout) */
  timeout_ms?: number;
}

/**
 * WebSocket connection configuration for resume progress
 */
export interface ResumeProgressWebSocketConfig {
  /** User ID for WebSocket connection */
  userId: string;
  /** WebSocket URL (defaults to current host) */
  wsUrl?: string;
  /** Whether to automatically connect on mount */
  autoConnect?: boolean;
  /** Whether to automatically reconnect on disconnect */
  autoReconnect?: boolean;
  /** Maximum number of reconnection attempts */
  maxReconnectAttempts?: number;
  /** Delay between reconnection attempts (ms) */
  reconnectDelay?: number;
}

/**
 * Stage display configuration
 *
 * Defines how each processing stage should be displayed in the UI.
 */
export interface StageDisplayConfig {
  /** Display label for the stage */
  label: string;
  /** Icon name for the stage */
  icon: string;
  /** Color theme for the stage */
  color: 'blue' | 'green' | 'yellow' | 'gray' | 'red';
  /** Description of what happens in this stage */
  description: string;
}

/**
 * Map of stage configurations for UI display
 */
export interface StageDisplayConfigMap {
  [key in ResumeProgressStage]: StageDisplayConfig;
}

/**
 * Progress statistics for monitoring
 */
export interface ProgressStatistics {
  /** Total number of resumes processed */
  total_processed: number;
  /** Number of successful completions */
  successful_count: number;
  /** Number of failures */
  failed_count: number;
  /** Average processing time per resume (milliseconds) */
  avg_processing_time_ms: number;
  /** Fastest processing time (milliseconds) */
  fastest_processing_time_ms: number;
  /** Slowest processing time (milliseconds) */
  slowest_processing_time_ms: number;
  /** Processing time distribution by stage */
  stage_times: Record<ResumeProgressStage, number>;
}

/**
 * Progress event for React state updates
 */
export interface ResumeProgressEvent {
  /** Type of event */
  type: 'start' | 'progress' | 'complete' | 'error' | 'cancel';
  /** Resume ID associated with the event */
  resume_id?: string;
  /** Current progress data */
  data: ResumeProgressState | BatchProcessingState;
  /** Timestamp when the event occurred */
  timestamp: string;
}
