import React, { useState, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Stack,
  Avatar,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { organizationsClient } from '@/api/organizations';

/**
 * Upload state interface
 */
interface UploadState {
  file: File | null;
  uploading: boolean;
  progress: number;
  error: string | null;
  success: boolean;
  logoUrl: string | null;
}

/**
 * LogoUpload Component Props
 */
interface LogoUploadProps {
  /** Current organization ID */
  organizationId: string;
  /** Current logo URL (if any) */
  currentLogoUrl?: string | null;
  /** Callback when upload completes successfully */
  onUploadComplete?: (logoUrl: string) => void;
  /** Callback when upload fails */
  onUploadError?: (error: string) => void;
  /** Maximum file size in bytes (default: 5MB) */
  maxFileSize?: number;
  /** Accepted file types */
  acceptedFileTypes?: string[];
  /** API endpoint URL for logo upload */
  uploadUrl?: string;
}

/**
 * LogoUpload Component
 *
 * Provides logo upload functionality with:
 * - File type validation (PNG, JPG, JPEG, SVG)
 * - File size validation (configurable, default 5MB)
 * - Upload progress tracking
 * - Image preview
 * - Error handling and display
 * - Success state with logo URL
 *
 * @example
 * ```tsx
 * <LogoUpload
 *   organizationId="org-123"
 *   currentLogoUrl="https://example.com/current-logo.png"
 *   onUploadComplete={(url) => console.log('Logo uploaded:', url)}
 *   onUploadError={(error) => console.error('Upload failed:', error)}
 * />
 * ```
 */
const LogoUpload: React.FC<LogoUploadProps> = ({
  organizationId,
  currentLogoUrl = null,
  onUploadComplete,
  onUploadError,
  maxFileSize = 5 * 1024 * 1024, // 5MB
  acceptedFileTypes = ['.png', '.jpg', '.jpeg', '.svg'],
  uploadUrl = '/api/branding/upload-logo',
}) => {
  const { t } = useTranslation();

  const [uploadState, setUploadState] = useState<UploadState>({
    file: null,
    uploading: false,
    progress: 0,
    error: null,
    success: false,
    logoUrl: currentLogoUrl,
  });

  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
      logoUrl: currentLogoUrl,
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [currentLogoUrl]);

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
        logoUrl: currentLogoUrl,
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
    [validateFile, onUploadError, currentLogoUrl]
  );

  /**
   * Upload file to backend
   */
  const uploadFile = useCallback(
    async (file: File) => {
      setUploadState((prev) => ({ ...prev, uploading: true, progress: 0 }));

      const formData = new FormData();
      formData.append('file', file);
      formData.append('organization_id', organizationId);

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
          if (xhr.status === 200 || xhr.status === 201) {
            const response = JSON.parse(xhr.responseText);
            const logoUrl = response.logo_url || response.url;

            setUploadState({
              file,
              uploading: false,
              progress: 100,
              error: null,
              success: true,
              logoUrl,
            });

            onUploadComplete?.(logoUrl);
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
        const apiUrl = import.meta.env.VITE_API_URL ?? '';
        xhr.open('POST', `${apiUrl}${uploadUrl}`);
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
    [organizationId, uploadUrl, onUploadComplete, onUploadError, t]
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
   * Handle delete logo
   */
  const handleDeleteLogo = useCallback(() => {
    setUploadState({
      file: null,
      uploading: false,
      progress: 0,
      error: null,
      success: false,
      logoUrl: null,
    });
    onUploadComplete?.('');
  }, [onUploadComplete]);

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
            {t('organization.logo.uploadSuccess')}
          </Alert>
        )}

        {/* Logo Preview Area */}
        {uploadState.logoUrl && !uploadState.success && !uploadState.error && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, mb: 3 }}>
            <Avatar
              src={uploadState.logoUrl}
              alt="Organization Logo"
              variant="rounded"
              sx={{
                width: 120,
                height: 120,
                border: '2px solid',
                borderColor: 'divider',
              }}
            >
              <BusinessIcon sx={{ fontSize: 60 }} />
            </Avatar>
            <Typography variant="body2" color="text.secondary">
              {t('organization.logo.currentLogo')}
            </Typography>
          </Box>
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
              {uploadState.logoUrl ? (
                <UploadIcon
                  sx={{
                    fontSize: 48,
                    color: isDragging ? 'primary.main' : 'action.disabled',
                    transition: 'color 0.2s',
                  }}
                />
              ) : (
                <BusinessIcon
                  sx={{
                    fontSize: 64,
                    color: isDragging ? 'primary.main' : 'action.disabled',
                    transition: 'color 0.2s',
                  }}
                />
              )}
            </Box>

            {/* Main Text */}
            <Typography variant="h6" align="center" gutterBottom fontWeight={600}>
              {uploadState.uploading
                ? t('upload.uploader.uploading')
                : isDragging
                  ? t('upload.uploader.dragDrop')
                  : uploadState.logoUrl
                    ? t('organization.logo.replaceLogo')
                    : t('organization.logo.uploadLogo')}
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
                <Box
                  key={type}
                  sx={{
                    px: 1.5,
                    py: 0.5,
                    borderRadius: 1,
                    bgcolor: isDragging ? 'primary.main' : 'action.hover',
                    color: isDragging ? 'primary.contrastText' : 'text.primary',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                  }}
                >
                  {type.toUpperCase().replace('.', '')}
                </Box>
              ))}
              <Box
                sx={{
                  px: 1.5,
                  py: 0.5,
                  borderRadius: 1,
                  bgcolor: isDragging ? 'primary.main' : 'action.hover',
                  color: isDragging ? 'primary.contrastText' : 'text.primary',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                }}
              >
                Max {(maxFileSize / (1024 * 1024)).toFixed(0)}MB
              </Box>
            </Stack>

            {/* Action Buttons */}
            {!uploadState.uploading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
                <Button
                  variant="outlined"
                  size="large"
                  startIcon={<UploadIcon />}
                  onClick={(e) => {
                    e.stopPropagation();
                    fileInputRef.current?.click();
                  }}
                  disabled={uploadState.uploading}
                >
                  {uploadState.logoUrl ? t('common.replace') : t('upload.uploader.chooseFile')}
                </Button>
                {uploadState.logoUrl && (
                  <Button
                    variant="outlined"
                    size="large"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteLogo();
                    }}
                    disabled={uploadState.uploading}
                  >
                    {t('common.remove')}
                  </Button>
                )}
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
              <BusinessIcon color="action" />
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
          {t('organization.logo.helpText', {
            maxSize: (maxFileSize / (1024 * 1024)).toFixed(0),
            formats: acceptedFileTypes.join(', ')
          })}
        </Typography>
      )}
    </Box>
  );
};

export default LogoUpload;
