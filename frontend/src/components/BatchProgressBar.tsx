/**
 * BatchProgressBar Component
 *
 * A reusable component for displaying batch upload/processing progress with
 * per-file status tracking. Integrates with WebSocket progress updates via
 * the useWebSocketProgress hook for real-time status display.
 *
 * @example
 * ```tsx
 * <BatchProgressBar
 *   total={100}
 *   completed={50}
 *   failed={5}
 *   files={[
 *     { id: '1', filename: 'resume1.pdf', status: 'complete', progress: 100 },
 *     { id: '2', filename: 'resume2.pdf', status: 'uploading', progress: 45 },
 *     { id: '3', filename: 'resume3.pdf', status: 'error', progress: 0, error: 'Invalid format' },
 *   ]}
 * />
 * ```
 */

import React from 'react';
import {
  Box,
  Typography,
  LinearProgress,
  Chip,
  CircularProgress,
  Tooltip,
  Paper,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  CloudUpload as UploadingIcon,
  Description as FileIcon,
  Warning as WarningIcon,
  ContentCopy as DuplicateIcon,
} from '@mui/icons-material';
import type { ResumeProgressStage, ResumeProcessingState } from '@/types/resume-progress';

/**
 * File status types for batch processing
 */
export type FileStatus = 'pending' | 'parsing' | 'analyzing' | 'ranking' | 'complete' | 'error' | 'duplicate';

/**
 * Individual file progress item
 */
export interface FileProgressItem {
  /** Unique identifier for the file */
  id: string;
  /** Original filename */
  filename: string;
  /** File size in bytes */
  size?: number;
  /** Current processing status */
  status: FileStatus;
  /** Progress percentage (0-100) */
  progress: number;
  /** Error message if status is 'error' */
  error?: string;
  /** Whether this file is a duplicate of another */
  isDuplicate?: boolean;
  /** Original file ID if this is a duplicate */
  duplicateOf?: string;
  /** Additional metadata from WebSocket updates */
  metadata?: Record<string, unknown>;
}

/**
 * Props for BatchProgressBar component
 */
export interface BatchProgressBarProps {
  /** Total number of files in batch */
  total: number;
  /** Number of completed files */
  completed: number;
  /** Number of failed files */
  failed: number;
  /** Number of duplicate files detected */
  duplicates?: number;
  /** Individual file progress items */
  files: FileProgressItem[];
  /** Overall progress percentage (0-100) */
  overallProgress?: number;
  /** Whether batch is currently processing */
  isActive?: boolean;
  /** Whether to show compact view (without file list) */
  compact?: boolean;
  /** Maximum height for file list */
  maxHeight?: number | string;
  /** Callback when a file row is clicked */
  onFileClick?: (file: FileProgressItem) => void;
  /** Custom className for styling */
  className?: string;
  /** Whether to show per-file progress bars */
  showFileProgress?: boolean;
  /** Label for the progress header */
  label?: string;
  /** Resume processing states from WebSocket (for real-time updates) */
  resumeStates?: Record<string, ResumeProcessingState>;
}

/**
 * Get status configuration for a file status
 */
const getStatusConfig = (status: FileStatus): {
  color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
  icon: React.ReactNode;
  label: string;
} => {
  switch (status) {
    case 'pending':
      return {
        color: 'default',
        icon: <PendingIcon fontSize="small" />,
        label: 'Pending',
      };
    case 'parsing':
      return {
        color: 'info',
        icon: <CircularProgress size={14} />,
        label: 'Parsing',
      };
    case 'analyzing':
      return {
        color: 'info',
        icon: <CircularProgress size={14} />,
        label: 'Analyzing',
      };
    case 'ranking':
      return {
        color: 'primary',
        icon: <CircularProgress size={14} />,
        label: 'Ranking',
      };
    case 'complete':
      return {
        color: 'success',
        icon: <CheckIcon fontSize="small" />,
        label: 'Complete',
      };
    case 'error':
      return {
        color: 'error',
        icon: <ErrorIcon fontSize="small" />,
        label: 'Error',
      };
    case 'duplicate':
      return {
        color: 'warning',
        icon: <DuplicateIcon fontSize="small" />,
        label: 'Duplicate',
      };
    default:
      return {
        color: 'default',
        icon: <FileIcon fontSize="small" />,
        label: status,
      };
  }
};

/**
 * Format file size for display
 */
const formatFileSize = (bytes?: number): string => {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/**
 * Truncate filename for display
 */
const truncateFilename = (filename: string, maxLength: number = 30): string => {
  if (filename.length <= maxLength) return filename;
  const ext = filename.split('.').pop() || '';
  const nameWithoutExt = filename.slice(0, -(ext.length + 1));
  const truncated = nameWithoutExt.slice(0, maxLength - ext.length - 4);
  return `${truncated}...${ext}`;
};

/**
 * File progress row component
 */
interface FileProgressRowProps {
  file: FileProgressItem;
  showProgress: boolean;
  onClick?: (file: FileProgressItem) => void;
  resumeState?: ResumeProcessingState;
}

const FileProgressRow: React.FC<FileProgressRowProps> = ({
  file,
  showProgress,
  onClick,
  resumeState,
}) => {
  const statusConfig = getStatusConfig(file.status);
  const displayProgress = resumeState?.progress ?? file.progress;
  const displayStatus = file.isDuplicate ? 'duplicate' : file.status;
  const finalConfig = getStatusConfig(displayStatus);

  const isProcessing = ['parsing', 'analyzing', 'ranking'].includes(file.status);

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        py: 1,
        px: 1.5,
        borderBottom: '1px solid',
        borderColor: 'divider',
        '&:last-child': { borderBottom: 'none' },
        '&:hover': onClick ? { bgcolor: 'action.hover' } : undefined,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'background-color 0.15s ease',
      }}
      onClick={() => onClick?.(file)}
    >
      {/* Status Icon */}
      <Box sx={{ display: 'flex', alignItems: 'center', mr: 1.5, minWidth: 24 }}>
        {finalConfig.icon}
      </Box>

      {/* Filename */}
      <Tooltip title={file.filename} placement="top-start">
        <Typography
          variant="body2"
          sx={{
            flexGrow: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            color: file.status === 'error' ? 'error.main' : 'text.primary',
          }}
        >
          {truncateFilename(file.filename)}
        </Typography>
      </Tooltip>

      {/* File Size (optional) */}
      {file.size !== undefined && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ ml: 1, display: { xs: 'none', sm: 'inline' } }}
        >
          {formatFileSize(file.size)}
        </Typography>
      )}

      {/* Progress or Status */}
      <Box sx={{ display: 'flex', alignItems: 'center', ml: 2, minWidth: 100 }}>
        {isProcessing && showProgress ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
            <LinearProgress
              variant="determinate"
              value={displayProgress}
              sx={{
                flexGrow: 1,
                height: 6,
                borderRadius: 3,
                bgcolor: 'action.hover',
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ minWidth: 35 }}>
              {displayProgress}%
            </Typography>
          </Box>
        ) : (
          <Chip
            size="small"
            label={finalConfig.label}
            color={finalConfig.color}
            variant={file.status === 'pending' ? 'outlined' : 'filled'}
            sx={{ height: 24 }}
          />
        )}
      </Box>

      {/* Error message */}
      {file.status === 'error' && file.error && (
        <Tooltip title={file.error}>
          <WarningIcon color="error" fontSize="small" sx={{ ml: 1 }} />
        </Tooltip>
      )}
    </Box>
  );
};

/**
 * BatchProgressBar Component
 *
 * Displays batch processing progress with overall stats and per-file status.
 */
const BatchProgressBar: React.FC<BatchProgressBarProps> = ({
  total,
  completed,
  failed,
  duplicates = 0,
  files,
  overallProgress,
  isActive = false,
  compact = false,
  maxHeight = 300,
  onFileClick,
  className,
  showFileProgress = true,
  label = 'Batch Progress',
  resumeStates,
}) => {
  // Calculate overall progress if not provided
  const calculatedProgress =
    overallProgress ?? (total > 0 ? Math.round((completed / total) * 100) : 0);

  // Calculate stats
  const processing = files.filter((f) =>
    ['parsing', 'analyzing', 'ranking'].includes(f.status)
  ).length;
  const pending = files.filter((f) => f.status === 'pending').length;

  // Compact view - just progress bar and stats
  if (compact) {
    return (
      <Box className={className}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {label}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {completed}/{total} files
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={calculatedProgress}
          sx={{
            height: 8,
            borderRadius: 4,
            bgcolor: 'action.hover',
            '& .MuiLinearProgress-bar': {
              borderRadius: 4,
            },
          }}
        />
        <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
          {processing > 0 && (
            <Typography variant="caption" color="info.main">
              {processing} processing
            </Typography>
          )}
          {failed > 0 && (
            <Typography variant="caption" color="error.main">
              {failed} failed
            </Typography>
          )}
          {duplicates > 0 && (
            <Typography variant="caption" color="warning.main">
              {duplicates} duplicates
            </Typography>
          )}
        </Box>
      </Box>
    );
  }

  return (
    <Paper
      className={className}
      sx={{
        p: 2,
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="subtitle1" component="h3">
          {label}
        </Typography>
        {isActive && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CircularProgress size={16} />
            <Typography variant="body2" color="info.main">
              Processing...
            </Typography>
          </Box>
        )}
      </Box>

      {/* Overall Progress */}
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
          <Typography variant="body2" color="text.secondary">
            Overall Progress
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {calculatedProgress}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={calculatedProgress}
          sx={{
            height: 10,
            borderRadius: 5,
            bgcolor: 'action.hover',
            '& .MuiLinearProgress-bar': {
              borderRadius: 5,
            },
          }}
        />
      </Box>

      {/* Stats Row */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: 'repeat(2, 1fr)',
            sm: 'repeat(5, 1fr)',
          },
          gap: 1.5,
          mb: 2,
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h6" color="text.primary">
            {total}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Total
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h6" color="success.main">
            {completed}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Completed
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h6" color="info.main">
            {processing}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Processing
          </Typography>
        </Box>
        {duplicates > 0 && (
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" color="warning.main">
              {duplicates}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Duplicates
            </Typography>
          </Box>
        )}
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h6" color="error.main">
            {failed}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Failed
          </Typography>
        </Box>
      </Box>

      {/* File List */}
      {files.length > 0 && (
        <Box
          sx={{
            maxHeight,
            overflow: 'auto',
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1,
          }}
        >
          {files.map((file) => (
            <FileProgressRow
              key={file.id}
              file={file}
              showProgress={showFileProgress}
              onClick={onFileClick}
              resumeState={resumeStates?.[file.id]}
            />
          ))}
        </Box>
      )}

      {/* Empty State */}
      {files.length === 0 && (
        <Box sx={{ py: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            No files in batch
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default BatchProgressBar;
