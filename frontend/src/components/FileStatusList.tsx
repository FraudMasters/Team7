/**
 * FileStatusList Component
 *
 * A reusable component for displaying detailed file status in batch operations.
 * Shows each file with its processing status, including parsing/analyzing/complete/
 * failed/duplicate states with appropriate icons and visual indicators.
 *
 * @example
 * ```tsx
 * <FileStatusList
 *   files={[
 *     { id: '1', filename: 'resume1.pdf', status: 'complete', progress: 100 },
 *     { id: '2', filename: 'resume2.pdf', status: 'analyzing', progress: 45 },
 *     { id: '3', filename: 'resume3.pdf', status: 'error', progress: 0, error: 'Invalid format' },
 *     { id: '4', filename: 'resume4.pdf', status: 'complete', isDuplicate: true },
 *   ]}
 *   onFileClick={(file) => console.log('Clicked:', file)}
 * />
 * ```
 */

import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  CircularProgress,
  Tooltip,
  IconButton,
  LinearProgress,
  Paper,
  Alert,
  Button,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  Description as FileIcon,
  Warning as WarningIcon,
  ContentCopy as DuplicateIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Folder as FolderIcon,
  BugReport as DebugIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import type { ResumeProcessingState } from '@/types/resume-progress';

/**
 * File status types for batch processing
 */
export type FileListStatus =
  | 'pending'
  | 'uploading'
  | 'parsing'
  | 'analyzing'
  | 'ranking'
  | 'complete'
  | 'error'
  | 'cancelled'
  | 'duplicate';

/**
 * Individual file item with detailed status information
 */
export interface FileStatusItem {
  /** Unique identifier for the file */
  id: string;
  /** Original filename */
  filename: string;
  /** File size in bytes */
  size?: number;
  /** Current processing status */
  status: FileListStatus;
  /** Progress percentage (0-100) */
  progress?: number;
  /** Error message if status is 'error' */
  error?: string;
  /** Error details for debugging */
  errorDetails?: string;
  /** Whether this file is a duplicate of another */
  isDuplicate?: boolean;
  /** Original file ID if this is a duplicate */
  duplicateOf?: string;
  /** Original filename if this is a duplicate */
  duplicateOfFilename?: string;
  /** Similarity score if duplicate (0-100) */
  duplicateSimilarity?: number;
  /** Match type for duplicates ('exact' | 'near') */
  duplicateMatchType?: 'exact' | 'near';
  /** Source of the file (upload, zip, email) */
  source?: 'upload' | 'zip' | 'email';
  /** ZIP file ID if extracted from archive */
  zipFileId?: string;
  /** Processing stage message */
  stageMessage?: string;
  /** Additional metadata */
  metadata?: Record<string, unknown>;
  /** Timestamp when processing started */
  startedAt?: string;
  /** Timestamp when processing completed */
  completedAt?: string;
  /** Resume ID after successful processing */
  resumeId?: string;
}

/**
 * Props for FileStatusList component
 */
export interface FileStatusListProps {
  /** Array of file items to display */
  files: FileStatusItem[];
  /** Resume processing states from WebSocket (for real-time updates) */
  resumeStates?: Record<string, ResumeProcessingState>;
  /** Whether to show file sizes */
  showSizes?: boolean;
  /** Whether to show progress bars for active files */
  showProgress?: boolean;
  /** Whether to show duplicate badges */
  showDuplicateBadges?: boolean;
  /** Whether to show source indicators (zip/email) */
  showSourceIndicators?: boolean;
  /** Whether the list is in a loading state */
  isLoading?: boolean;
  /** Whether actions are disabled */
  disabled?: boolean;
  /** Maximum height for the list (scrollable if exceeded) */
  maxHeight?: number | string;
  /** Compact mode with less padding */
  compact?: boolean;
  /** Show border around the list */
  bordered?: boolean;
  /** Callback when a file row is clicked */
  onFileClick?: (file: FileStatusItem) => void;
  /** Callback when retry is clicked for failed file */
  onRetry?: (file: FileStatusItem) => void;
  /** Callback when remove is clicked */
  onRemove?: (file: FileStatusItem) => void;
  /** Callback when view details is clicked */
  onViewDetails?: (file: FileStatusItem) => void;
  /** Callback when duplicate is accepted */
  onAcceptDuplicate?: (file: FileStatusItem) => void;
  /** Callback when duplicate is rejected */
  onRejectDuplicate?: (file: FileStatusItem) => void;
  /** Custom empty state message */
  emptyMessage?: string;
  /** Custom className for styling */
  className?: string;
  /** Title for the list header */
  title?: string;
  /** Whether to show the header */
  showHeader?: boolean;
  /** Filter by status */
  statusFilter?: FileListStatus | 'all';
  /** Group files by status */
  groupByStatus?: boolean;
}

/**
 * Get status configuration for a file status
 */
const getStatusConfig = (status: FileListStatus, isDuplicate?: boolean): {
  color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning';
  icon: React.ReactNode;
  label: string;
  showProgress: boolean;
} => {
  // If duplicate, override status
  if (isDuplicate && status === 'complete') {
    return {
      color: 'warning',
      icon: <DuplicateIcon fontSize="small" />,
      label: 'Duplicate',
      showProgress: false,
    };
  }

  switch (status) {
    case 'pending':
      return {
        color: 'default',
        icon: <PendingIcon fontSize="small" />,
        label: 'Pending',
        showProgress: false,
      };
    case 'uploading':
      return {
        color: 'info',
        icon: <CircularProgress size={16} />,
        label: 'Uploading',
        showProgress: true,
      };
    case 'parsing':
      return {
        color: 'info',
        icon: <CircularProgress size={16} />,
        label: 'Parsing',
        showProgress: true,
      };
    case 'analyzing':
      return {
        color: 'info',
        icon: <CircularProgress size={16} />,
        label: 'Analyzing',
        showProgress: true,
      };
    case 'ranking':
      return {
        color: 'primary',
        icon: <CircularProgress size={16} />,
        label: 'Ranking',
        showProgress: true,
      };
    case 'complete':
      return {
        color: 'success',
        icon: <CheckIcon fontSize="small" />,
        label: 'Complete',
        showProgress: false,
      };
    case 'error':
      return {
        color: 'error',
        icon: <ErrorIcon fontSize="small" />,
        label: 'Error',
        showProgress: false,
      };
    case 'cancelled':
      return {
        color: 'default',
        icon: <WarningIcon fontSize="small" />,
        label: 'Cancelled',
        showProgress: false,
      };
    case 'duplicate':
      return {
        color: 'warning',
        icon: <DuplicateIcon fontSize="small" />,
        label: 'Duplicate',
        showProgress: false,
      };
    default:
      return {
        color: 'default',
        icon: <FileIcon fontSize="small" />,
        label: status,
        showProgress: false,
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
const truncateFilename = (filename: string, maxLength: number = 35): string => {
  if (filename.length <= maxLength) return filename;
  const ext = filename.split('.').pop() || '';
  const nameWithoutExt = filename.slice(0, -(ext.length + 1));
  const truncated = nameWithoutExt.slice(0, maxLength - ext.length - 4);
  return `${truncated}...${ext}`;
};

/**
 * Get source icon for file
 */
const getSourceIcon = (source?: 'upload' | 'zip' | 'email'): React.ReactNode => {
  switch (source) {
    case 'zip':
      return (
        <Tooltip title="Extracted from ZIP">
          <FolderIcon fontSize="small" color="action" sx={{ ml: 0.5 }} />
        </Tooltip>
      );
    case 'email':
      return (
        <Tooltip title="From email attachment">
          <FileIcon fontSize="small" color="action" sx={{ ml: 0.5 }} />
        </Tooltip>
      );
    default:
      return null;
  }
};

/**
 * Individual file status row component
 */
interface FileStatusRowProps {
  file: FileStatusItem;
  resumeState?: ResumeProcessingState;
  showSize: boolean;
  showProgress: boolean;
  showDuplicateBadges: boolean;
  showSourceIndicators: boolean;
  disabled: boolean;
  compact: boolean;
  onFileClick?: (file: FileStatusItem) => void;
  onRetry?: (file: FileStatusItem) => void;
  onRemove?: (file: FileStatusItem) => void;
  onViewDetails?: (file: FileStatusItem) => void;
  onAcceptDuplicate?: (file: FileStatusItem) => void;
  onRejectDuplicate?: (file: FileStatusItem) => void;
}

const FileStatusRow: React.FC<FileStatusRowProps> = ({
  file,
  resumeState,
  showSize,
  showProgress,
  showDuplicateBadges,
  showSourceIndicators,
  disabled,
  compact,
  onFileClick,
  onRetry,
  onRemove,
  onViewDetails,
  onAcceptDuplicate,
  onRejectDuplicate,
}) => {
  const displayProgress = resumeState?.progress ?? file.progress ?? 0;
  const displayMessage = resumeState?.message ?? file.stageMessage;
  const isDuplicate = file.isDuplicate || file.status === 'duplicate';
  const statusConfig = getStatusConfig(file.status, isDuplicate);

  const isActive = ['uploading', 'parsing', 'analyzing', 'ranking'].includes(file.status);
  const isFailed = file.status === 'error';
  const isComplete = file.status === 'complete';

  const handleClick = () => {
    if (!disabled && onFileClick) {
      onFileClick(file);
    }
  };

  return (
    <ListItem
      sx={{
        px: compact ? 1 : 2,
        py: compact ? 0.75 : 1.25,
        borderBottom: '1px solid',
        borderColor: 'divider',
        '&:last-child': { borderBottom: 'none' },
        '&:hover': onFileClick ? { bgcolor: 'action.hover' } : undefined,
        cursor: onFileClick ? 'pointer' : 'default',
        bgcolor: isDuplicate ? 'warning.lighter' : isFailed ? 'error.lighter' : 'inherit',
        transition: 'background-color 0.15s ease',
      }}
      onClick={handleClick}
    >
      {/* Status Icon */}
      <ListItemIcon sx={{ minWidth: 36 }}>
        {statusConfig.icon}
      </ListItemIcon>

      {/* File Info */}
      <ListItemText
        primary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Tooltip title={file.filename} placement="top-start">
              <Typography
                variant="body2"
                sx={{
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  color: isFailed ? 'error.main' : 'text.primary',
                  fontWeight: isDuplicate ? 500 : 400,
                }}
              >
                {truncateFilename(file.filename)}
              </Typography>
            </Tooltip>
            {showSourceIndicators && getSourceIcon(file.source)}
            {showDuplicateBadges && isDuplicate && (
              <Chip
                size="small"
                label={file.duplicateMatchType === 'exact' ? 'Exact match' : 'Similar'}
                color="warning"
                variant="outlined"
                sx={{ height: 20, fontSize: '0.65rem', ml: 0.5 }}
              />
            )}
          </Box>
        }
        secondary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.25 }}>
            {showSize && file.size !== undefined && (
              <Typography variant="caption" color="text.secondary">
                {formatFileSize(file.size)}
              </Typography>
            )}
            {displayMessage && isActive && (
              <Typography variant="caption" color="info.main">
                {displayMessage}
              </Typography>
            )}
            {isDuplicate && file.duplicateOfFilename && (
              <Typography variant="caption" color="warning.main">
                Duplicate of: {truncateFilename(file.duplicateOfFilename, 20)}
              </Typography>
            )}
            {isFailed && file.error && (
              <Typography variant="caption" color="error.main">
                {file.error}
              </Typography>
            )}
          </Box>
        }
      />

      {/* Progress Bar (for active files) */}
      {showProgress && isActive && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120, mr: 1 }}>
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
          <Typography variant="caption" color="text.secondary" sx={{ minWidth: 30 }}>
            {displayProgress}%
          </Typography>
        </Box>
      )}

      {/* Status Chip (for non-active files) */}
      {!isActive && (
        <Box sx={{ mr: 1 }}>
          <Chip
            size="small"
            label={statusConfig.label}
            color={statusConfig.color}
            variant={file.status === 'pending' || file.status === 'cancelled' ? 'outlined' : 'filled'}
            sx={{ height: 24 }}
          />
        </Box>
      )}

      {/* Actions */}
      <ListItemSecondaryAction>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {/* View Details Button */}
          {isComplete && file.resumeId && onViewDetails && (
            <Tooltip title="View details">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onViewDetails(file);
                }}
                disabled={disabled}
                sx={{ minWidth: 32, minHeight: 32 }}
              >
                <ViewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}

          {/* Duplicate Actions */}
          {isDuplicate && onAcceptDuplicate && onRejectDuplicate && (
            <>
              <Tooltip title="Accept duplicate">
                <IconButton
                  size="small"
                  color="success"
                  onClick={(e) => {
                    e.stopPropagation();
                    onAcceptDuplicate(file);
                  }}
                  disabled={disabled}
                  sx={{ minWidth: 32, minHeight: 32 }}
                >
                  <CheckIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Reject duplicate">
                <IconButton
                  size="small"
                  color="error"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRejectDuplicate(file);
                  }}
                  disabled={disabled}
                  sx={{ minWidth: 32, minHeight: 32 }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </>
          )}

          {/* Retry Button */}
          {isFailed && onRetry && (
            <Tooltip title="Retry">
              <IconButton
                size="small"
                color="primary"
                onClick={(e) => {
                  e.stopPropagation();
                  onRetry(file);
                }}
                disabled={disabled}
                sx={{ minWidth: 32, minHeight: 32 }}
              >
                <RefreshIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}

          {/* Remove Button */}
          {onRemove && !isActive && (
            <Tooltip title="Remove">
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(file);
                }}
                disabled={disabled}
                sx={{ minWidth: 32, minHeight: 32 }}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </ListItemSecondaryAction>
    </ListItem>
  );
};

/**
 * Calculate status counts from files
 */
const getStatusCounts = (files: FileStatusItem[]) => {
  const counts = {
    total: files.length,
    pending: 0,
    uploading: 0,
    parsing: 0,
    analyzing: 0,
    ranking: 0,
    complete: 0,
    error: 0,
    cancelled: 0,
    duplicate: 0,
    processing: 0,
    failed: 0,
  };

  files.forEach((file) => {
    if (file.status in counts) {
      counts[file.status as keyof typeof counts]++;
    }

    if (['uploading', 'parsing', 'analyzing', 'ranking'].includes(file.status)) {
      counts.processing++;
    }
    if (file.status === 'error' || file.status === 'cancelled') {
      counts.failed++;
    }
    if (file.isDuplicate || file.status === 'duplicate') {
      counts.duplicate++;
    }
  });

  return counts;
};

/**
 * FileStatusList Component
 *
 * Displays a list of files with detailed status information for batch operations.
 */
const FileStatusList: React.FC<FileStatusListProps> = ({
  files,
  resumeStates,
  showSizes = true,
  showProgress = true,
  showDuplicateBadges = true,
  showSourceIndicators = true,
  isLoading = false,
  disabled = false,
  maxHeight = 400,
  compact = false,
  bordered = true,
  onFileClick,
  onRetry,
  onRemove,
  onViewDetails,
  onAcceptDuplicate,
  onRejectDuplicate,
  emptyMessage = 'No files added yet',
  className,
  title = 'Files',
  showHeader = true,
  statusFilter = 'all',
  groupByStatus = false,
}) => {
  // Filter files if statusFilter is set
  const filteredFiles = statusFilter === 'all'
    ? files
    : files.filter((f) => {
        if (statusFilter === 'duplicate') {
          return f.isDuplicate || f.status === 'duplicate';
        }
        return f.status === statusFilter;
      });

  // Group files by status if enabled
  const groupedFiles = groupByStatus
    ? {
        processing: filteredFiles.filter((f) =>
          ['uploading', 'parsing', 'analyzing', 'ranking'].includes(f.status)
        ),
        complete: filteredFiles.filter((f) => f.status === 'complete' && !f.isDuplicate),
        duplicate: filteredFiles.filter((f) => f.isDuplicate || f.status === 'duplicate'),
        error: filteredFiles.filter((f) => f.status === 'error'),
        pending: filteredFiles.filter((f) => f.status === 'pending' || f.status === 'cancelled'),
      }
    : null;

  const statusCounts = getStatusCounts(files);

  // Loading state
  if (isLoading) {
    return (
      <Paper
        className={className}
        sx={{
          p: 3,
          textAlign: 'center',
          border: bordered ? '1px solid' : 'none',
          borderColor: 'divider',
        }}
      >
        <CircularProgress size={24} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Loading files...
        </Typography>
      </Paper>
    );
  }

  // Empty state
  if (files.length === 0) {
    return (
      <Paper
        className={className}
        sx={{
          p: 3,
          textAlign: 'center',
          border: bordered ? '1px solid' : 'none',
          borderColor: 'divider',
        }}
      >
        <FileIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
        <Typography variant="body1" color="text.secondary">
          {emptyMessage}
        </Typography>
      </Paper>
    );
  }

  // No files match filter
  if (filteredFiles.length === 0 && statusFilter !== 'all') {
    return (
      <Paper
        className={className}
        sx={{
          p: 3,
          border: bordered ? '1px solid' : 'none',
          borderColor: 'divider',
        }}
      >
        {showHeader && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle1">{title}</Typography>
            <Chip size="small" label={`${files.length} total`} />
          </Box>
        )}
        <Typography variant="body2" color="text.secondary" align="center">
          No files match the current filter
        </Typography>
      </Paper>
    );
  }

  // Render grouped files
  if (groupByStatus && groupedFiles) {
    const groups = [
      { key: 'processing', label: 'Processing', files: groupedFiles.processing, color: 'info.main' as const },
      { key: 'complete', label: 'Completed', files: groupedFiles.complete, color: 'success.main' as const },
      { key: 'duplicate', label: 'Duplicates', files: groupedFiles.duplicate, color: 'warning.main' as const },
      { key: 'error', label: 'Failed', files: groupedFiles.error, color: 'error.main' as const },
      { key: 'pending', label: 'Pending', files: groupedFiles.pending, color: 'text.secondary' as const },
    ].filter((g) => g.files.length > 0);

    return (
      <Paper
        className={className}
        sx={{
          border: bordered ? '1px solid' : 'none',
          borderColor: 'divider',
          overflow: 'hidden',
        }}
      >
        {showHeader && (
          <Box sx={{ p: compact ? 1 : 2, borderBottom: '1px solid', borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="subtitle1">{title}</Typography>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                {statusCounts.processing > 0 && (
                  <Chip size="small" label={`${statusCounts.processing} processing`} color="info" />
                )}
                {statusCounts.error > 0 && (
                  <Chip size="small" label={`${statusCounts.error} failed`} color="error" />
                )}
                {statusCounts.duplicate > 0 && (
                  <Chip size="small" label={`${statusCounts.duplicate} duplicates`} color="warning" />
                )}
              </Box>
            </Box>
          </Box>
        )}

        <Box sx={{ maxHeight, overflow: 'auto' }}>
          {groups.map((group) => (
            <Box key={group.key}>
              <Box
                sx={{
                  px: compact ? 1 : 2,
                  py: 0.75,
                  bgcolor: 'action.hover',
                  borderBottom: '1px solid',
                  borderColor: 'divider',
                }}
              >
                <Typography
                  variant="caption"
                  sx={{ fontWeight: 600, color: group.color, textTransform: 'uppercase' }}
                >
                  {group.label} ({group.files.length})
                </Typography>
              </Box>
              <List disablePadding>
                {group.files.map((file) => (
                  <FileStatusRow
                    key={file.id}
                    file={file}
                    resumeState={resumeStates?.[file.id]}
                    showSize={showSizes}
                    showProgress={showProgress}
                    showDuplicateBadges={showDuplicateBadges}
                    showSourceIndicators={showSourceIndicators}
                    disabled={disabled}
                    compact={compact}
                    onFileClick={onFileClick}
                    onRetry={onRetry}
                    onRemove={onRemove}
                    onViewDetails={onViewDetails}
                    onAcceptDuplicate={onAcceptDuplicate}
                    onRejectDuplicate={onRejectDuplicate}
                  />
                ))}
              </List>
            </Box>
          ))}
        </Box>
      </Paper>
    );
  }

  // Render flat list
  return (
    <Paper
      className={className}
      sx={{
        border: bordered ? '1px solid' : 'none',
        borderColor: 'divider',
        overflow: 'hidden',
      }}
    >
      {showHeader && (
        <Box sx={{ p: compact ? 1 : 2, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="subtitle1">{title}</Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Chip size="small" label={`${filteredFiles.length} files`} />
              {statusCounts.processing > 0 && (
                <Chip size="small" label={`${statusCounts.processing} processing`} color="info" />
              )}
              {statusCounts.error > 0 && (
                <Chip size="small" label={`${statusCounts.error} failed`} color="error" />
              )}
              {statusCounts.duplicate > 0 && (
                <Chip size="small" label={`${statusCounts.duplicate} duplicates`} color="warning" />
              )}
            </Box>
          </Box>
        </Box>
      )}

      <Box sx={{ maxHeight, overflow: 'auto' }}>
        <List disablePadding>
          {filteredFiles.map((file) => (
            <FileStatusRow
              key={file.id}
              file={file}
              resumeState={resumeStates?.[file.id]}
              showSize={showSizes}
              showProgress={showProgress}
              showDuplicateBadges={showDuplicateBadges}
              showSourceIndicators={showSourceIndicators}
              disabled={disabled}
              compact={compact}
              onFileClick={onFileClick}
              onRetry={onRetry}
              onRemove={onRemove}
              onViewDetails={onViewDetails}
              onAcceptDuplicate={onAcceptDuplicate}
              onRejectDuplicate={onRejectDuplicate}
            />
          ))}
        </List>
      </Box>
    </Paper>
  );
};

export default FileStatusList;
export type { FileStatusListProps, FileStatusItem, FileListStatus };
