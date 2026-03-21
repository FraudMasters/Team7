import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Stack,
  Divider,
  Alert,
  CircularProgress,
  Collapse,
  Grid,
  Card,
  CardContent,
  Chip,
  Tooltip,
  TextField,
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Description as FileIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { apiClient } from '@/api';

/**
 * File status in the upload queue
 */
type FileStatus = 'pending' | 'uploading' | 'processing' | 'completed' | 'error';

/**
 * Individual file in the upload queue
 */
interface FileQueueItem {
  /** File object */
  file: File;
  /** Unique ID for tracking */
  id: string;
  /** Current status */
  status: FileStatus;
  /** Error message if failed */
  error?: string;
  /** Resume ID if successfully uploaded */
  resumeId?: string;
}

/**
 * Batch upload response from backend
 */
interface BatchUploadResponse {
  batch_id: string;
  total_files: number;
  status: string;
  message: string;
}

/**
 * Batch status response from backend
 */
interface BatchStatusResponse {
  batch_id: string;
  status: string;
  total_files: number;
  processed_files: number;
  failed_files: number;
  progress_percentage: number;
  created_at?: string;
  completed_at?: string;
  error_message?: string;
}

/**
 * Individual file result from batch processing
 */
interface BatchFileItem {
  resume_id: string;
  filename: string;
  status: string;
  error?: string;
}

/**
 * Batch results response from backend
 */
interface BatchResultsResponse {
  batch_id: string;
  status: string;
  total_files: number;
  successful: number;
  failed: number;
  files: BatchFileItem[];
}

/**
 * BulkResumeUpload Component Props
 */
interface BulkResumeUploadProps {
  /** Callback when upload completes successfully */
  onUploadComplete?: (results: BatchResultsResponse) => void;
  /** Callback when individual file upload fails */
  onUploadError?: (error: string) => void;
  /** Vacancy ID to associate with uploaded resumes */
  vacancyId?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Maximum number of files allowed in batch */
  maxFiles?: number;
  /** Maximum file size in MB */
  maxFileSize?: number;
  /** Allowed file extensions */
  allowedExtensions?: string[];
}

/**
 * BulkResumeUpload Component
 *
 * Provides drag-and-drop interface for bulk resume upload:
 * - Drag and drop multiple resume files or ZIP archives
 * - Visual feedback for drag state and file selection
 * - Progress tracking with completed/remaining counts
 * - Detailed error handling and success notifications
 * - Support for PDF, DOCX, and ZIP file formats
 *
 * @example
 * ```tsx
 * <BulkResumeUpload
 *   onUploadComplete={(results) => console.log('Uploaded:', results.successful)}
 *   vacancyId="vacancy-123"
 *   maxFiles={50}
 * />
 * ```
 */
const BulkResumeUpload: React.FC<BulkResumeUploadProps> = ({
  onUploadComplete,
  onUploadError,
  vacancyId,
  disabled = false,
  maxFiles = 100,
  maxFileSize = 10,
  allowedExtensions = ['.pdf', '.docx', '.doc', '.zip'],
}) => {
  const { t } = useTranslation();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // State for file queue and upload status
  const [fileQueue, setFileQueue] = useState<FileQueueItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [batchStatus, setBatchStatus] = useState<BatchStatusResponse | null>(null);
  const [batchResults, setBatchResults] = useState<BatchResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Polling interval reference for cleanup
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Validate file extension
   */
  const isValidFileType = useCallback(
    (file: File): boolean => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      return allowedExtensions.includes(ext);
    },
    [allowedExtensions]
  );

  /**
   * Validate file size
   */
  const isValidFileSize = useCallback(
    (file: File): boolean => {
      const sizeMB = file.size / (1024 * 1024);
      return sizeMB <= maxFileSize;
    },
    [maxFileSize]
  );

  /**
   * Add files to queue
   */
  const addFilesToQueue = useCallback(
    (files: File[]) => {
      if (disabled || isUploading) {
        return;
      }

      setError(null);

      // Validate file count
      const newTotalFiles = fileQueue.length + files.length;
      if (newTotalFiles > maxFiles) {
        setError(t('bulkUpload.tooManyFiles', { max: maxFiles }));
        return;
      }

      // Validate and add files
      const validFiles: FileQueueItem[] = [];
      const invalidFiles: string[] = [];

      files.forEach((file) => {
        if (!isValidFileType(file)) {
          invalidFiles.push(`${file.name} (${t('bulkUpload.invalidType')})`);
        } else if (!isValidFileSize(file)) {
          invalidFiles.push(`${file.name} (${t('bulkUpload.tooLarge', { max: maxFileSize })})`);
        } else {
          validFiles.push({
            file,
            id: `${file.name}-${Date.now()}-${Math.random()}`,
            status: 'pending',
          });
        }
      });

      if (invalidFiles.length > 0) {
        setError(
          t('bulkUpload.someFilesInvalid', {
            count: invalidFiles.length,
            files: invalidFiles.slice(0, 3).join(', '),
          })
        );
      }

      if (validFiles.length > 0) {
        setFileQueue((prev) => [...prev, ...validFiles]);
      }
    },
    [
      disabled,
      isUploading,
      fileQueue.length,
      maxFiles,
      isValidFileType,
      isValidFileSize,
      t,
    ]
  );

  /**
   * Handle file input change
   */
  const handleFileInputChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files;
      if (files && files.length > 0) {
        addFilesToQueue(Array.from(files));
      }
      // Reset input so same files can be selected again
      event.target.value = '';
    },
    [addFilesToQueue]
  );

  /**
   * Handle drag events
   */
  const handleDragEnter = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    if (!disabled && !isUploading) {
      setIsDragOver(true);
    }
  }, [disabled, isUploading]);

  const handleDragLeave = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      event.stopPropagation();
      setIsDragOver(false);

      if (disabled || isUploading) {
        return;
      }

      const files = Array.from(event.dataTransfer.files);
      if (files.length > 0) {
        addFilesToQueue(files);
      }
    },
    [disabled, isUploading, addFilesToQueue]
  );

  /**
   * Remove file from queue
   */
  const removeFileFromQueue = useCallback(
    (fileId: string) => {
      if (disabled || isUploading) {
        return;
      }
      setFileQueue((prev) => prev.filter((item) => item.id !== fileId));
      setError(null);
    },
    [disabled, isUploading]
  );

  /**
   * Clear all files from queue
   */
  const clearQueue = useCallback(() => {
    if (disabled || isUploading) {
      return;
    }
    setFileQueue([]);
    setBatchStatus(null);
    setBatchResults(null);
    setError(null);
  }, [disabled, isUploading]);

  /**
   * Poll batch status
   */
  const pollBatchStatus = useCallback(
    async (batchId: string) => {
      try {
        const response = await apiClient.getAxiosInstance().get<BatchStatusResponse>(
          `/api/batch/${batchId}`
        );
        const status = response.data;
        setBatchStatus(status);

        // Check if batch is complete
        if (status.status === 'completed' || status.status === 'failed') {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }

          setIsUploading(false);

          // Fetch final results
          try {
            const resultsResponse = await apiClient.getAxiosInstance().get<BatchResultsResponse>(
              `/api/batch/${batchId}/results`
            );
            setBatchResults(resultsResponse.data);
            onUploadComplete?.(resultsResponse.data);

            // Show error if batch failed
            if (status.status === 'failed') {
              setError(status.error_message || t('bulkUpload.batchFailed'));
            }
          } catch (err) {
            const errorMessage = err instanceof Error ? err.message : t('bulkUpload.resultsError');
            setError(errorMessage);
            onUploadError?.(errorMessage);
          }
        }
      } catch (err) {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        setIsUploading(false);
        const errorMessage = err instanceof Error ? err.message : t('bulkUpload.statusError');
        setError(errorMessage);
        onUploadError?.(errorMessage);
      }
    },
    [onUploadComplete, onUploadError, t]
  );

  /**
   * Start batch upload
   */
  const handleUpload = useCallback(async () => {
    if (fileQueue.length === 0 || isUploading || disabled) {
      return;
    }

    setIsUploading(true);
    setError(null);
    setBatchStatus(null);
    setBatchResults(null);

    // Mark all files as uploading
    setFileQueue((prev) =>
      prev.map((item) => ({
        ...item,
        status: 'uploading',
      }))
    );

    try {
      // Create FormData with files
      const formData = new FormData();
      fileQueue.forEach((item) => {
        formData.append('files', item.file);
      });

      // Add optional vacancy ID
      if (vacancyId) {
        formData.append('vacancy_id', vacancyId);
      }

      // Upload files
      const response = await apiClient.getAxiosInstance().post<BatchUploadResponse>(
        '/api/batch/upload',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      const batchData = response.data;

      // Start polling for status
      setBatchStatus({
        batch_id: batchData.batch_id,
        status: batchData.status,
        total_files: batchData.total_files,
        processed_files: 0,
        failed_files: 0,
        progress_percentage: 0,
      });

      // Poll status every 2 seconds
      pollingIntervalRef.current = setInterval(() => {
        pollBatchStatus(batchData.batch_id);
      }, 2000);

      // Initial status check
      await pollBatchStatus(batchData.batch_id);
    } catch (err) {
      setIsUploading(false);
      setFileQueue((prev) =>
        prev.map((item) => ({
          ...item,
          status: 'error',
          error: err instanceof Error ? err.message : t('bulkUpload.uploadError'),
        }))
      );
      const errorMessage = err instanceof Error ? err.message : t('bulkUpload.uploadError');
      setError(errorMessage);
      onUploadError?.(errorMessage);
    }
  }, [fileQueue, isUploading, disabled, vacancyId, pollBatchStatus, onUploadError, t]);

  // Clean up polling interval on unmount
  React.useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const hasFiles = fileQueue.length > 0;
  const canUpload = hasFiles && !isUploading && !disabled;
  const progress = batchStatus?.progress_percentage || 0;
  const remainingFiles = batchStatus ? batchStatus.total_files - batchStatus.processed_files : 0;

  return (
    <Stack spacing={2}>
      {/* Upload Zone */}
      <Paper
        elevation={1}
        sx={{
          p: 3,
          border: 2,
          borderStyle: 'dashed',
          borderColor: isDragOver ? 'primary.main' : 'divider',
          bgcolor: isDragOver ? 'primary.50' : 'background.paper',
          cursor: disabled || isUploading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease-in-out',
        }}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => {
          if (!disabled && !isUploading && fileInputRef.current) {
            fileInputRef.current.click();
          }
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={allowedExtensions.join(',')}
          onChange={handleFileInputChange}
          disabled={disabled || isUploading}
          style={{ display: 'none' }}
        />

        <Stack spacing={2} alignItems="center" sx={{ py: 3 }}>
          <CloudUploadIcon
            sx={{
              fontSize: 64,
              color: isDragOver ? 'primary.main' : 'text.secondary',
            }}
          />
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              {t('bulkUpload.title')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('bulkUpload.dragDrop')}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              {t('bulkUpload.allowedFormats', { formats: allowedExtensions.join(', ') })}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              {t('bulkUpload.maxSize', { max: maxFileSize, count: maxFiles })}
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<CloudUploadIcon />}
            disabled={disabled || isUploading}
            onClick={(e) => {
              e.stopPropagation();
              if (fileInputRef.current) {
                fileInputRef.current.click();
              }
            }}
          >
            {t('bulkUpload.browseFiles')}
          </Button>
        </Stack>
      </Paper>

      {/* File Queue */}
      {hasFiles && (
        <Paper elevation={1} sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <FileIcon sx={{ mr: 1, fontSize: 24, color: 'primary.main' }} />
              <Typography variant="h6" fontWeight={600}>
                {t('bulkUpload.fileQueue', { count: fileQueue.length })}
              </Typography>
            </Box>
            <Chip
              label={`${fileQueue.length} ${fileQueue.length === 1 ? t('bulkUpload.file') : t('bulkUpload.files')}`}
              size="medium"
              color="primary"
              variant="outlined"
            />
          </Box>
          <Divider sx={{ mb: 2 }} />

          {/* Progress Bar */}
          {isUploading && batchStatus && (
            <Box sx={{ mb: 2 }}>
              <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  {t('bulkUpload.progress')}:
                </Typography>
                <Typography variant="body2" fontWeight={600} color="success.main">
                  {batchStatus.processed_files} {t('bulkUpload.completed')}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  /
                </Typography>
                <Typography variant="body2" fontWeight={600} color="primary.main">
                  {batchStatus.total_files} {t('bulkUpload.total')}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  •
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('bulkUpload.remaining')}:
                </Typography>
                <Typography variant="body2" fontWeight={600} color="warning.main">
                  {remainingFiles}
                </Typography>
                <Typography variant="body2" fontWeight={600} color="primary.main">
                  ({progress}%)
                </Typography>
              </Stack>
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'action.hover',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 4,
                  },
                }}
              />
            </Box>
          )}

          {/* File List */}
          <Grid container spacing={2}>
            {fileQueue.map((item) => {
              const isLoading = item.status === 'uploading' || item.status === 'processing';
              const isError = item.status === 'error';
              const isSuccess = item.status === 'completed';

              return (
                <Grid item xs={12} sm={6} md={4} key={item.id}>
                  <Card
                    sx={{
                      border: 1,
                      borderColor: isError
                        ? 'error.main'
                        : isSuccess
                          ? 'success.main'
                          : 'divider',
                      bgcolor: isError
                        ? 'error.50'
                        : isSuccess
                          ? 'success.50'
                          : 'background.paper',
                    }}
                  >
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      <Stack spacing={1} direction="row" alignItems="flex-start">
                        {/* Status Icon */}
                        <Box sx={{ mt: 0.5 }}>
                          {isLoading ? (
                            <CircularProgress size={20} />
                          ) : isError ? (
                            <ErrorIcon sx={{ fontSize: 20, color: 'error.main' }} />
                          ) : isSuccess ? (
                            <CheckCircleIcon sx={{ fontSize: 20, color: 'success.main' }} />
                          ) : (
                            <FileIcon sx={{ fontSize: 20, color: 'text.secondary' }} />
                          )}
                        </Box>

                        {/* File Info */}
                        <Box sx={{ flex: 1, minWidth: 0 }}>
                          <Typography
                            variant="body2"
                            fontWeight={500}
                            sx={{
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {item.file.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {(item.file.size / 1024 / 1024).toFixed(2)} MB
                          </Typography>
                          {item.error && (
                            <Typography variant="caption" color="error.main" sx={{ display: 'block' }}>
                              {item.error}
                            </Typography>
                          )}
                        </Box>

                        {/* Delete Button */}
                        {!isUploading && (
                          <Tooltip title={t('bulkUpload.removeFile')}>
                            <Box
                              sx={{
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                              }}
                              onClick={() => removeFileFromQueue(item.id)}
                            >
                              <DeleteIcon
                                sx={{ fontSize: 18, color: 'text.secondary', '&:hover': { color: 'error.main' } }}
                              />
                            </Box>
                          </Tooltip>
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>

          {/* Action Buttons */}
          <Stack direction="row" spacing={2} sx={{ mt: 2 }} justifyContent="flex-end">
            <Button
              variant="outlined"
              onClick={clearQueue}
              disabled={disabled || isUploading}
              color="secondary"
            >
              {t('bulkUpload.clearAll')}
            </Button>
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={!canUpload}
              startIcon={isUploading ? <CircularProgress size={16} /> : <CloudUploadIcon />}
            >
              {isUploading ? t('bulkUpload.uploading') : t('bulkUpload.uploadAll')}
            </Button>
          </Stack>
        </Paper>
      )}

      {/* Error Alert */}
      <Collapse in={!!error}>
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      </Collapse>

      {/* Success Alert */}
      <Collapse in={!!batchResults && batchResults.status === 'completed'}>
        <Alert severity="success" sx={{ mt: 2 }}>
          <Typography variant="body2">
            {t('bulkUpload.uploadSuccess', {
              successful: batchResults?.successful,
              total: batchResults?.total_files,
            })}
          </Typography>
        </Alert>
      </Collapse>
    </Stack>
  );
};

export default BulkResumeUpload;
