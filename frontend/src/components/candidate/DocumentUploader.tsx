import React, { useState, useCallback, useRef, forwardRef, useImperativeHandle, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { config } from '@/config';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Chip,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Description as FileIcon,
  Delete as DeleteIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

/**
 * Document type categories
 */
export type DocumentType =
  | 'certificate'
  | 'diploma'
  | 'reference'
  | 'portfolio'
  | 'other';

/**
 * File upload state interface
 */
interface UploadState {
  file: File | null;
  uploading: boolean;
  progress: number;
  error: string | null;
  success: boolean;
  documentId: string | null;
  documentType: DocumentType;
}

/**
 * Imperative handle exposed by DocumentUploader
 */
export interface DocumentUploaderHandle {
  /**
   * Trigger the file input click to open file picker
   */
  triggerUpload: () => void;
  /**
   * Cancel current upload and reset state
   */
  cancelUpload: () => void;
}

/**
 * DocumentUploader Component Props
 */
interface DocumentUploaderProps {
  /** API endpoint URL for document upload */
  uploadUrl?: string;
  /** Maximum file size in bytes (default: 10MB) */
  maxFileSize?: number;
  /** Accepted file types */
  acceptedFileTypes?: string[];
  /** Show document type selector */
  showDocumentTypeSelector?: boolean;
  /** Default document type */
  defaultDocumentType?: DocumentType;
  /** Callback when upload completes successfully */
  onUploadComplete?: (documentId: string, documentType: DocumentType) => void;
  /** Callback when upload fails */
  onUploadError?: (error: string) => void;
  /** Callback when uploading state changes */
  onUploadingChange?: (isUploading: boolean) => void;
  /** Callback when upload starts */
  onUploadStart?: () => void;
}

/**
 * DocumentUploader Component
 *
 * Provides drag-and-drop document upload functionality with:
 * - File type validation (PDF, DOCX, JPG, PNG)
 * - File size validation (configurable, default 10MB)
 * - Document type categorization
 * - Upload progress tracking
 * - Error handling and display
 * - Success state with document ID
 *
 * @example
 * ```tsx
 * const uploaderRef = useRef<DocumentUploaderHandle>(null);
 * <DocumentUploader
 *   ref={uploaderRef}
 *   uploadUrl={`${config.api.url}/api/candidate/documents/upload`}
 *   onUploadComplete={(id, type) => console.log('Uploaded:', id, type)}
 *   showDocumentTypeSelector={true}
 * />
 *
 * // Programmatic trigger
 * uploaderRef.current?.triggerUpload();
 * uploaderRef.current?.cancelUpload();
 * ```
 */
const DocumentUploader = forwardRef<DocumentUploaderHandle, DocumentUploaderProps>(({
  uploadUrl = `${config.api.url}/api/candidate/documents/upload`,
  maxFileSize = 10 * 1024 * 1024, // 10MB
  acceptedFileTypes = ['.pdf', '.docx', '.jpg', '.jpeg', '.png'],
  showDocumentTypeSelector = true,
  defaultDocumentType = 'other',
  onUploadComplete,
  onUploadError,
  onUploadingChange,
  onUploadStart,
}, ref) => {
  const { t } = useTranslation();

  const [uploadState, setUploadState] = useState<UploadState>({
    file: null,
    uploading: false,
    progress: 0,
    error: null,
    success: false,
    documentId: null,
    documentType: defaultDocumentType,
  });

  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Notify parent of uploading state changes
   */
  useEffect(() => {
    onUploadingChange?.(uploadState.uploading);
  }, [uploadState.uploading, onUploadingChange]);

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
      documentId: null,
      documentType: defaultDocumentType,
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [defaultDocumentType]);

  /**
   * Expose methods via ref for parent component access
   */
  useImperativeHandle(ref, () => ({
    triggerUpload: () => {
      if (!uploadState.uploading) {
        fileInputRef.current?.click();
      }
    },
    cancelUpload: () => {
      handleReset();
    },
  }), [uploadState.uploading, handleReset]);

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
      setUploadState((prev) => ({
        file: null,
        uploading: false,
        progress: 0,
        error: null,
        success: false,
        documentId: null,
        documentType: prev.documentType,
      }));

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
   * Handle document type change
   */
  const handleDocumentTypeChange = useCallback((event: SelectChangeEvent<DocumentType>) => {
    setUploadState((prev) => ({
      ...prev,
      documentType: event.target.value as DocumentType,
    }));
  }, []);

  /**
   * Upload file to backend
   */
  const uploadFile = useCallback(
    async (file: File) => {
      setUploadState((prev) => ({ ...prev, uploading: true, progress: 0 }));

      // Notify parent that upload has started
      onUploadStart?.();

      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_type', uploadState.documentType);

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
          if (xhr.status === 201 || xhr.status === 200) {
            const response = JSON.parse(xhr.responseText);
            const documentId = response.id || response.document_id;

            setUploadState((prev) => ({
              ...prev,
              file,
              uploading: false,
              progress: 100,
              error: null,
              success: true,
              documentId,
            }));

            onUploadComplete?.(documentId, uploadState.documentType);
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
    [uploadUrl, uploadState.documentType, onUploadComplete, onUploadError, onUploadStart, t]
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
   * Format file size for display
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  /**
   * Get document type label
   */
  const getDocumentTypeLabel = (type: DocumentType): string => {
    const labels: Record<DocumentType, string> = {
      certificate: t('candidate.documents.types.certificate', 'Certificate'),
      diploma: t('candidate.documents.types.diploma', 'Diploma'),
      reference: t('candidate.documents.types.reference', 'Reference Letter'),
      portfolio: t('candidate.documents.types.portfolio', 'Portfolio'),
      other: t('candidate.documents.types.other', 'Other'),
    };
    return labels[type];
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Document Type Selector */}
      {showDocumentTypeSelector && !uploadState.success && (
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel id="document-type-label">
            {t('candidate.documents.documentType', 'Document Type')}
          </InputLabel>
          <Select
            labelId="document-type-label"
            id="document-type-select"
            value={uploadState.documentType}
            label={t('candidate.documents.documentType', 'Document Type')}
            onChange={handleDocumentTypeChange}
            disabled={uploadState.uploading}
          >
            <MenuItem value="certificate">{getDocumentTypeLabel('certificate')}</MenuItem>
            <MenuItem value="diploma">{getDocumentTypeLabel('diploma')}</MenuItem>
            <MenuItem value="reference">{getDocumentTypeLabel('reference')}</MenuItem>
            <MenuItem value="portfolio">{getDocumentTypeLabel('portfolio')}</MenuItem>
            <MenuItem value="other">{getDocumentTypeLabel('other')}</MenuItem>
          </Select>
        </FormControl>
      )}

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
                {t('candidate.documents.uploadAnother', 'Upload Another')}
              </Button>
            }
          >
            {t('candidate.documents.uploadSuccess', { documentId: uploadState.documentId })}
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
                ? t('candidate.documents.uploading', 'Uploading Document...')
                : isDragging
                  ? t('candidate.documents.dropHere', 'Drop file here')
                  : t('candidate.documents.uploadDocument', 'Upload Document')}
            </Typography>

            {/* Subtitle */}
            <Typography
              variant="body2"
              align="center"
              color="text.secondary"
              paragraph
            >
              {uploadState.uploading
                ? t('candidate.documents.pleaseWait', 'Please wait while we upload your document...')
                : t('candidate.documents.dragOrClick', 'Drag and drop a file here, or click to browse')}
            </Typography>

            {/* File Type Info */}
            <Stack direction="row" spacing={1} justifyContent="center" mb={2} flexWrap="wrap">
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
                  {t('candidate.documents.chooseFile', 'Choose File')}
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
          {t('candidate.documents.supportedFormats', {
            formats: acceptedFileTypes.join(', ').toUpperCase(),
            maxSize: (maxFileSize / (1024 * 1024)).toFixed(0)
          })}
        </Typography>
      )}
    </Box>
  );
});

DocumentUploader.displayName = 'DocumentUploader';

export default DocumentUploader;
