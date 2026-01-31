import React, { useState, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Chip,
  Stack,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as FileIcon,
  Delete as DeleteIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

/**
 * File upload state interface
 */
interface UploadState {
  file: File | null;
  uploading: boolean;
  progress: number;
  error: string | null;
  success: boolean;
  resumeId: string | null;
}

/**
 * ResumeUploader Component Props
 */
interface ResumeUploaderProps {
  /** API endpoint URL for resume upload */
  uploadUrl?: string;
  /** Maximum file size in bytes (default: 10MB) */
  maxFileSize?: number;
  /** Accepted file types */
  acceptedFileTypes?: string[];
  /** Callback when upload completes successfully */
  onUploadComplete?: (resumeId: string) => void;
  /** Callback when upload fails */
  onUploadError?: (error: string) => void;
}

/**
 * ResumeUploader Component
 *
 * Provides drag-and-drop resume upload functionality with:
 * - File type validation (PDF, DOCX)
 * - File size validation (configurable, default 10MB)
 * - Upload progress tracking
 * - Error handling and display
 * - Success state with resume ID
 *
 * @example
 * ```tsx
 * <ResumeUploader
 *   uploadUrl="http://localhost:8000/api/resumes/upload"
 *   onUploadComplete={(id) => navigate(`/results/${id}`)}
 * />
 * ```
 */
const ResumeUploader: React.FC<ResumeUploaderProps> = ({
  uploadUrl = 'http://localhost:8000/api/resumes/upload',
  maxFileSize = 10 * 1024 * 1024, // 10MB
  acceptedFileTypes = ['.pdf', '.docx'],
  onUploadComplete,
  onUploadError,
}) => {
  const { t } = useTranslation();

  const [uploadState, setUploadState] = useState<UploadState>({
    file: null,
    uploading: false,
    progress: 0,
    error: null,
    success: false,
    resumeId: null,
  });

  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Validate file type and size
   */
  const validateFile = useCallback(
    (file: File): string | null => {
      // Check file extension
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!acceptedFileTypes.includes(fileExtension)) {
        return t('errors.invalidFileType', { fileTypes: acceptedFileTypes.join(', ') });
      }

      // Check file size
      if (file.size > maxFileSize) {
        const maxSizeMB = (maxFileSize / (1024 * 1024)).toFixed(0);
        return t('errors.fileTooLarge', { maxSize: maxSizeMB });
      }

      return null;
    },
    [acceptedFileTypes, maxFileSize, t]
  );

  /**
   * Handle file selection (from input or drag-drop)
   */
  const handleFileSelect = useCallback(
    (file: File) => {
      // Reset state
      setUploadState({
        file: null,
        uploading: false,
        progress: 0,
        error: null,
        success: false,
        resumeId: null,
      });

      // Validate file
      const validationError = validateFile(file);
      if (validationError) {
        setUploadState((prev) => ({ ...prev, error: validationError }));
        onUploadError?.(validationError);
        return;
      }

      // Set file and start upload
      setUploadState((prev) => ({ ...prev, file }));
      uploadFile(file);
    },
    [validateFile, onUploadError]
  );

  /**
   * Upload file to backend
   */
  const uploadFile = useCallback(
    async (file: File) => {
      setUploadState((prev) => ({ ...prev, uploading: true, progress: 0 }));

      const formData = new FormData();
      formData.append('file', file);

      try {
        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener('progress', (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            setUploadState((prev) => ({ ...prev, progress }));
          }
        });

        // Handle completion
        xhr.addEventListener('load', () => {
          if (xhr.status === 201) {
            const response = JSON.parse(xhr.responseText);
            const resumeId = response.id || response.resume_id;

            setUploadState({
              file,
              uploading: false,
              progress: 100,
              error: null,
              success: true,
              resumeId,
            });

            onUploadComplete?.(resumeId);
          } else {
            const error = xhr.responseText || t('errors.failedToUpload');
            setUploadState((prev) => ({
              ...prev,
              uploading: false,
              error: `${t('errors.failedToUpload')}: ${error}`,
            }));
            onUploadError?.(error);
          }
        });

        // Handle errors
        xhr.addEventListener('error', () => {
          const error = t('errors.network');
          setUploadState((prev) => ({
            ...prev,
            uploading: false,
            error,
          }));
          onUploadError?.(error);
        });

        xhr.addEventListener('abort', () => {
          setUploadState((prev) => ({
            ...prev,
            uploading: false,
            error: t('errors.uploadCancelled'),
          }));
        });

        // Send request
        xhr.open('POST', uploadUrl);
        xhr.send(formData);
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : t('errors.somethingWentWrong');
        setUploadState((prev) => ({
          ...prev,
          uploading: false,
          error: errorMessage,
        }));
        onUploadError?.(errorMessage);
      }
    },
    [uploadUrl, onUploadComplete, onUploadError, t]
  );

  /**
   * Handle drag events
   */
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      const files = e.dataTransfer.files;
      if (files.length > 0 && files[0]) {
        handleFileSelect(files[0]);
      }
    },
    [handleFileSelect]
  );

  /**
   * Handle file input change
   */
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0 && files[0]) {
        handleFileSelect(files[0]);
      }
    },
    [handleFileSelect]
  );

  /**
   * Reset upload state
   */
  const handleReset = useCallback(() => {
    setUploadState({
      file: null,
      uploading: false,
      progress: 0,
      error: null,
      success: false,
      resumeId: null,
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  /**
   * Format file size for display
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedFileTypes.join(',')}
        onChange={handleInputChange}
        style={{ display: 'none' }}
        disabled={uploadState.uploading}
      />

      <Paper
        elevation={2}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        sx={{
          p: 4,
          border: '2px dashed',
          borderColor: isDragging
            ? 'primary.main'
            : uploadState.error
              ? 'error.main'
              : uploadState.success
                ? 'success.main'
                : 'divider',
          bgcolor: isDragging ? 'action.hover' : 'background.paper',
          transition: 'all 0.2s ease-in-out',
          cursor: uploadState.uploading ? 'wait' : 'pointer',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Error Alert */}
        {uploadState.error && (
          <Alert
            severity="error"
            icon={<ErrorIcon />}
            sx={{ mb: 2 }}
            action={
              !uploadState.uploading && (
                <Button
                  color="inherit"
                  size="small"
                  onClick={handleReset}
                  disabled={uploadState.uploading}
                >
                  {t('common.tryAgain')}
                </Button>
              )
            }
          >
            {uploadState.error}
          </Alert>
        )}

        {/* Success Alert */}
        {uploadState.success && (
          <Alert
            severity="success"
            icon={<SuccessIcon />}
            sx={{ mb: 2 }}
            action={
              <Button
                color="inherit"
                size="small"
                onClick={handleReset}
                disabled={uploadState.uploading}
              >
                {t('upload.uploader.uploadAnother')}
              </Button>
            }
          >
            {t('upload.uploader.success', { resumeId: uploadState.resumeId })}
          </Alert>
        )}

        {/* Upload Area */}
        {!uploadState.success && !uploadState.error && (
          <Box
            onClick={() => !uploadState.uploading && fileInputRef.current?.click()}
          >
            {/* Upload Icon */}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                mb: 2,
              }}
            >
              <UploadIcon
                sx={{
                  fontSize: 64,
                  color: isDragging ? 'primary.main' : 'action.disabled',
                  transition: 'color 0.2s',
                }}
              />
            </Box>

            {/* Main Text */}
            <Typography variant="h6" align="center" gutterBottom fontWeight={600}>
              {uploadState.uploading
                ? t('upload.uploader.uploading')
                : isDragging
                  ? t('upload.uploader.dragDrop')
                  : t('upload.title')}
            </Typography>

            {/* Subtitle */}
            <Typography
              variant="body2"
              align="center"
              color="text.secondary"
              paragraph
            >
              {uploadState.uploading
                ? t('upload.uploader.pleaseWait')
                : t('upload.uploader.clickToBrowse')}
            </Typography>

            {/* File Type Info */}
            <Stack direction="row" spacing={1} justifyContent="center" mb={2}>
              {acceptedFileTypes.map((type) => (
                <Chip
                  key={type}
                  label={type.toUpperCase().replace('.', '')}
                  size="small"
                  variant="outlined"
                  color={isDragging ? 'primary' : 'default'}
                />
              ))}
              <Chip
                label={`Max ${(maxFileSize / (1024 * 1024)).toFixed(0)}MB`}
                size="small"
                variant="outlined"
                color={isDragging ? 'primary' : 'default'}
              />
            </Stack>

            {/* Browse Button */}
            {!uploadState.uploading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={<UploadIcon />}
                  onClick={(e) => {
                    e.stopPropagation();
                    fileInputRef.current?.click();
                  }}
                  disabled={uploadState.uploading}
                >
                  {t('upload.uploader.chooseFile')}
                </Button>
              </Box>
            )}
          </Box>
        )}

        {/* Selected File Info */}
        {uploadState.file && !uploadState.success && (
          <Box sx={{ mt: 2 }}>
            <Stack
              direction="row"
              spacing={2}
              alignItems="center"
              justifyContent="center"
            >
              <FileIcon color="action" />
              <Typography variant="body2" color="text.primary">
                <strong>{uploadState.file.name}</strong>
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ({formatFileSize(uploadState.file.size)})
              </Typography>
              {!uploadState.uploading && (
                <Button
                  size="small"
                  startIcon={<DeleteIcon />}
                  onClick={handleReset}
                  color="error"
                >
                  {t('common.remove')}
                </Button>
              )}
            </Stack>
          </Box>
        )}

        {/* Progress Bar */}
        {uploadState.uploading && (
          <Box sx={{ mt: 3 }}>
            <LinearProgress
              variant="determinate"
              value={uploadState.progress}
              sx={{ height: 8, borderRadius: 4 }}
            />
            <Typography
              variant="body2"
              align="center"
              color="text.secondary"
              sx={{ mt: 1 }}
            >
              {uploadState.progress}%
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Help Text */}
      {!uploadState.success && (
        <Typography
          variant="caption"
          color="text.secondary"
          align="center"
          display="block"
          sx={{ mt: 2 }}
        >
          {t('upload.uploader.supportedFormats', { maxSize: (maxFileSize / (1024 * 1024)).toFixed(0) })}
        </Typography>
      )}
    </Box>
  );
};

export default ResumeUploader;
