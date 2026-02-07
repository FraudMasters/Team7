import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Typography,
  Box,
  Paper,
  Button,
  ToggleButton,
  ToggleButtonGroup,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Chip,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { config } from '@/config';
import ErrorBoundary from '@components/ErrorBoundary';
import { useKeyboardNavigation } from '@hooks/useKeyboardNavigation';
import ResumeUploader, { ResumeUploaderHandle } from '@components/ResumeUploader';

const API_URL = (window as any).env?.REACT_APP_API_URL || config.api.url;

interface FileItem {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error' | 'cancelled';
  error?: string;
  progress?: number;
  abortController?: AbortController;
}

type UploadMode = 'single' | 'multiple';

/**
 * Unified Upload Page Component
 *
 * Provides a single interface for both single and multiple file uploads.
 * Users can switch between modes using toggle buttons.
 * - Single mode: Upload one resume and view results immediately
 * - Multiple mode: Upload multiple resumes in batch
 */
const UnifiedUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  // Upload mode state
  const [mode, setMode] = useState<UploadMode>('single');

  // Single file upload state
  const singleUploaderRef = useRef<ResumeUploaderHandle>(null);
  const [isSingleUploading, setIsSingleUploading] = useState(false);
  const [singleUploadError, setSingleUploadError] = useState<string | null>(null);

  // Multiple file upload state
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isMultipleUploading, setIsMultipleUploading] = useState(false);
  const [multipleUploadError, setMultipleUploadError] = useState<string | null>(null);
  const [multipleUploadSuccess, setMultipleUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  /**
   * Handle mode change
   */
  const handleModeChange = useCallback(
    (_event: React.MouseEvent<HTMLElement>, newMode: UploadMode | null) => {
      if (newMode) {
        setMode(newMode);
        // Clear errors when switching modes
        setSingleUploadError(null);
        setMultipleUploadError(null);
        setMultipleUploadSuccess(null);
      }
    },
    []
  );

  /**
   * Handle single file upload completion
   */
  const handleSingleUploadComplete = useCallback((resumeId: string) => {
    setSingleUploadError(null);
    navigate(`/results/${resumeId}`);
  }, [navigate]);

  /**
   * Handle single file upload error
   */
  const handleSingleUploadError = useCallback((error: string) => {
    setSingleUploadError(error);
  }, []);

  /**
   * Handle single file uploading state changes
   */
  const handleSingleUploadingChange = useCallback((uploading: boolean) => {
    setIsSingleUploading(uploading);
  }, []);

  /**
   * Handle file selection for multiple upload
   */
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || []);
    const newFiles: FileItem[] = selectedFiles.map((file) => ({
      file,
      id: `${Date.now()}-${Math.random()}`,
      status: 'pending',
      progress: 0,
      abortController: new AbortController(),
    }));
    setFiles((prev) => [...prev, ...newFiles]);
    setMultipleUploadError(null);
    setMultipleUploadSuccess(null);
    if (event.target) {
      event.target.value = '';
    }
  }, []);

  /**
   * Handle drag and drop for multiple upload
   */
  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const droppedFiles = Array.from(event.dataTransfer.files).filter((file) => {
      const ext = file.name.split('.').pop()?.toLowerCase();
      return ext === 'pdf' || ext === 'docx';
    });
    if (droppedFiles.length === 0) {
      setMultipleUploadError('Only PDF and DOCX files are allowed');
      return;
    }
    const newFiles: FileItem[] = droppedFiles.map((file) => ({
      file,
      id: `${Date.now()}-${Math.random()}`,
      status: 'pending',
      progress: 0,
      abortController: new AbortController(),
    }));
    setFiles((prev) => [...prev, ...newFiles]);
    setMultipleUploadError(null);
  }, []);

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  }, []);

  /**
   * Remove file from multiple upload list
   */
  const removeFile = useCallback((id: string) => {
    setFiles((prev) => {
      const file = prev.find((f) => f.id === id);
      if (file?.abortController) {
        file.abortController.abort();
      }
      return prev.filter((f) => f.id !== id);
    });
  }, []);

  /**
   * Cancel file upload
   */
  const cancelFileUpload = useCallback((id: string) => {
    setFiles((prev) =>
      prev.map((f) => {
        if (f.id === id && f.status === 'uploading') {
          if (f.abortController) {
            f.abortController.abort();
          }
          return { ...f, status: 'cancelled' as const, progress: 0 };
        }
        return f;
      })
    );
  }, []);

  /**
   * Clear all files
   */
  const clearAllFiles = useCallback(() => {
    setFiles((prev) => {
      prev.forEach((f) => {
        if (f.abortController) {
          f.abortController.abort();
        }
      });
      return [];
    });
    setMultipleUploadError(null);
    setMultipleUploadSuccess(null);
  }, []);

  /**
   * Retry failed uploads
   */
  const retryFailedUploads = useCallback(async () => {
    const failedFiles = files.filter((f) => f.status === 'error' || f.status === 'cancelled');
    if (failedFiles.length === 0) {
      setMultipleUploadError('No failed files to retry');
      return;
    }

    setIsMultipleUploading(true);
    setMultipleUploadError(null);

    setFiles((prev) =>
      prev.map((f) =>
        f.status === 'error' || f.status === 'cancelled'
          ? { ...f, status: 'uploading' as const, error: undefined, progress: 0, abortController: new AbortController() }
          : f
      )
    );

    try {
      const uploadPromises = failedFiles.map((fileItem) => uploadSingleFile(fileItem));
      const results = await Promise.all(uploadPromises);

      const successCount = results.filter((r) => r.success).length;
      const failureCount = results.filter((r) => !r.success).length;

      setFiles((prev) =>
        prev.map((f) => {
          const result = results.find((r) => r.id === f.id);
          if (!result) return f;
          if (result.success) {
            return { ...f, status: 'success' as const, progress: 100 };
          } else if (result.error === 'Cancelled') {
            return { ...f, status: 'cancelled' as const, progress: 0 };
          } else {
            return { ...f, status: 'error' as const, error: result.error || 'Upload failed', progress: 0 };
          }
        })
      );

      if (successCount > 0) {
        setMultipleUploadSuccess(`Successfully retried ${successCount} file${successCount !== 1 ? 's' : ''}`);
      }

      if (failureCount > 0) {
        setMultipleUploadError(`${failureCount} file(s) failed to retry`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Retry failed';
      setMultipleUploadError(errorMessage);
      setFiles((prev) =>
        prev.map((f) =>
          f.status === 'uploading' ? { ...f, status: 'error' as const, error: errorMessage, progress: 0 } : f
        )
      );
    } finally {
      setIsMultipleUploading(false);
    }
  }, [files]);

  /**
   * Upload a single file in multiple upload mode
   */
  const uploadSingleFile = useCallback((fileItem: FileItem): Promise<{ id: string; success: boolean; error?: string }> => {
    return new Promise((resolve) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setFiles((prev) =>
            prev.map((f) =>
              f.id === fileItem.id ? { ...f, progress } : f
            )
          );
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200 || xhr.status === 201) {
          resolve({ id: fileItem.id, success: true });
        } else {
          resolve({ id: fileItem.id, success: false, error: `HTTP ${xhr.status}` });
        }
      });

      xhr.addEventListener('error', () => {
        resolve({ id: fileItem.id, success: false, error: 'Network error' });
      });

      xhr.addEventListener('abort', () => {
        resolve({ id: fileItem.id, success: false, error: 'Cancelled' });
      });

      const formData = new FormData();
      formData.append('file', fileItem.file);

      xhr.open('POST', `${API_URL}/api/resumes/upload`);
      xhr.send(formData);
    });
  }, []);

  /**
   * Handle multiple file upload
   */
  const handleMultipleUpload = useCallback(async () => {
    if (files.length === 0) {
      setMultipleUploadError('Please select at least one file');
      return;
    }

    setIsMultipleUploading(true);
    setMultipleUploadError(null);
    setMultipleUploadSuccess(null);

    setFiles((prev) =>
      prev.map((f) => ({ ...f, status: 'uploading' as const, progress: 0, error: undefined }))
    );

    try {
      const uploadPromises = files
        .filter((f) => f.status !== 'cancelled')
        .map((fileItem) => uploadSingleFile(fileItem));

      const results = await Promise.all(uploadPromises);

      const successCount = results.filter((r) => r.success).length;
      const failureCount = results.filter((r) => !r.success).length;

      setFiles((prev) =>
        prev.map((f) => {
          const result = results.find((r) => r.id === f.id);
          if (!result) return f;
          if (result.success) {
            return { ...f, status: 'success' as const, progress: 100 };
          } else if (result.error === 'Cancelled') {
            return { ...f, status: 'cancelled' as const, progress: 0 };
          } else {
            return { ...f, status: 'error' as const, error: result.error || 'Upload failed', progress: 0 };
          }
        })
      );

      if (successCount > 0) {
        setMultipleUploadSuccess(`Successfully uploaded ${successCount} file${successCount !== 1 ? 's' : ''}`);
      }

      if (failureCount > 0) {
        setMultipleUploadError(`${failureCount} file(s) failed to upload`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setMultipleUploadError(errorMessage);
      setFiles((prev) =>
        prev.map((f) =>
          f.status === 'uploading' ? { ...f, status: 'error' as const, error: errorMessage, progress: 0 } : f
        )
      );
    } finally {
      setIsMultipleUploading(false);
    }
  }, [files, uploadSingleFile]);

  /**
   * Retry single file in multiple upload
   */
  const retrySingleFile = useCallback((id: string) => {
    setFiles((prev) =>
      prev.map((f) =>
        f.id === id
          ? { ...f, status: 'pending' as const, error: undefined }
          : f
      )
    );
    setMultipleUploadError(null);
  }, []);

  /**
   * Keyboard shortcuts
   */
  const handleTriggerUpload = useCallback(() => {
    if (mode === 'single') {
      singleUploaderRef.current?.triggerUpload();
    } else {
      fileInputRef.current?.click();
    }
  }, [mode]);

  const handleCancelUpload = useCallback(() => {
    if (mode === 'single') {
      singleUploaderRef.current?.cancelUpload();
    } else {
      clearAllFiles();
    }
  }, [mode, clearAllFiles]);

  useKeyboardNavigation({
    shortcuts: [
      {
        id: 'upload-trigger',
        key: 'u',
        modifiers: ['Ctrl'],
        handler: handleTriggerUpload,
        description: 'Trigger file upload',
      },
      {
        id: 'upload-cancel',
        key: 'Escape',
        handler: handleCancelUpload,
        description: 'Cancel upload',
      },
    ],
  });

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      files.forEach((f) => {
        if (f.abortController && f.status === 'uploading') {
          f.abortController.abort();
        }
      });
    };
  }, [files]);

  /**
   * Format file size for display
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('Unified upload page error:', error, errorInfo);
      }}
    >
      <Box sx={{ position: 'relative' }}>
        {/* Page Header */}
        <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
          {t('upload.title', { defaultValue: 'Upload Resume' })}
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          {t('upload.subtitle', { defaultValue: 'Upload your resume for AI-powered analysis' })}
        </Typography>

        {/* Keyboard Shortcuts Hint */}
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
          <strong>Keyboard shortcuts:</strong> Ctrl+U to upload, Esc to cancel
        </Typography>

        {/* Mode Toggle */}
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <ToggleButtonGroup
            value={mode}
            exclusive
            onChange={handleModeChange}
            aria-label="upload mode"
          >
            <ToggleButton value="single" aria-label="single file upload">
              Single File
            </ToggleButton>
            <ToggleButton value="multiple" aria-label="multiple file upload">
              Multiple Files
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {/* Single File Upload Mode */}
        {mode === 'single' && (
          <Paper elevation={1} sx={{ p: 4 }}>
            {singleUploadError && (
              <Alert
                severity="error"
                sx={{ mb: 2 }}
                action={
                  <Button
                    color="inherit"
                    size="small"
                    onClick={() => setSingleUploadError(null)}
                  >
                    Dismiss
                  </Button>
                }
              >
                {singleUploadError}
              </Alert>
            )}

            <ResumeUploader
              ref={singleUploaderRef}
              uploadUrl={`${config.api.url}/api/resumes/upload`}
              onUploadComplete={handleSingleUploadComplete}
              onUploadError={handleSingleUploadError}
              onUploadingChange={handleSingleUploadingChange}
            />
          </Paper>
        )}

        {/* Multiple File Upload Mode */}
        {mode === 'multiple' && (
          <Paper elevation={1} sx={{ p: 4 }}>
            {multipleUploadError && (
              <Alert
                severity="error"
                sx={{ mb: 2 }}
                action={
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      variant="contained"
                      color="primary"
                      onClick={retryFailedUploads}
                      disabled={isMultipleUploading}
                    >
                      Retry Failed
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      color="secondary"
                      onClick={() => {
                        setFiles((prev) => prev.filter((f) => f.status !== 'error' && f.status !== 'cancelled'));
                        setMultipleUploadError(null);
                      }}
                      disabled={isMultipleUploading}
                    >
                      Remove Failed
                    </Button>
                    <IconButton
                      size="small"
                      onClick={() => setMultipleUploadError(null)}
                      disabled={isMultipleUploading}
                    >
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  </Box>
                }
              >
                {multipleUploadError}
              </Alert>
            )}

            {multipleUploadSuccess && (
              <Alert
                severity="success"
                sx={{ mb: 2 }}
                onClose={() => setMultipleUploadSuccess(null)}
              >
                {multipleUploadSuccess}
              </Alert>
            )}

            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', md: files.length > 0 ? '1fr 1fr' : '1fr' },
                gap: 3,
              }}
            >
              {/* Upload Zone */}
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 3,
                }}
              >
                <Box
                  sx={{
                    border: '2px dashed',
                    borderColor: 'divider',
                    borderRadius: 2,
                    p: { xs: 3, md: 4 },
                    textAlign: 'center',
                    cursor: 'pointer',
                    '&:hover': {
                      borderColor: 'primary.main',
                      bgcolor: 'action.hover',
                    },
                  }}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.docx"
                    style={{ display: 'none' }}
                    onChange={handleFileSelect}
                    disabled={isMultipleUploading}
                  />
                  <UploadIcon
                    sx={{
                      fontSize: { xs: 36, md: 48 },
                      color: 'primary.main',
                      mb: 2,
                    }}
                  />
                  <Typography variant="h6" gutterBottom>
                    Drag & Drop Resume Files
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    or click to browse (PDF, DOCX)
                  </Typography>
                </Box>
              </Box>

              {/* File List */}
              {files.length > 0 && (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="subtitle1">
                      {files.length} file{files.length !== 1 ? 's' : ''} selected
                    </Typography>
                    <Button onClick={clearAllFiles} disabled={isMultipleUploading} size="small">
                      Clear All
                    </Button>
                  </Box>

                  {/* Overall Progress */}
                  {isMultipleUploading && (
                    <Box sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          Overall Progress
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {files.filter((f) => f.status === 'success').length} / {files.length}
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={
                          files.length > 0
                            ? files.reduce((sum, f) => sum + (f.progress || 0), 0) / files.length
                            : 0
                        }
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        {Math.round(
                          files.length > 0
                            ? files.reduce((sum, f) => sum + (f.progress || 0), 0) / files.length
                            : 0
                        )}% Complete
                      </Typography>
                    </Box>
                  )}

                  <TableContainer
                    sx={{
                      flexGrow: 1,
                      maxHeight: { xs: 300, md: 400 },
                      mb: 2,
                    }}
                  >
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell>Filename</TableCell>
                          <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Size</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell align="right">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {files.map((fileItem) => (
                          <React.Fragment key={fileItem.id}>
                            <TableRow>
                              <TableCell
                                sx={{
                                  maxWidth: { xs: 120, md: 200 },
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {fileItem.file.name}
                              </TableCell>
                              <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                                {formatFileSize(fileItem.file.size)}
                              </TableCell>
                              <TableCell>
                                {fileItem.status === 'success' && <CheckIcon color="success" fontSize="small" />}
                                {fileItem.status === 'error' && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <ErrorIcon color="error" fontSize="small" />
                                    <Tooltip title={fileItem.error || 'Upload failed'}>
                                      <Typography
                                        variant="caption"
                                        color="error"
                                        sx={{
                                          maxWidth: { xs: 80, md: 150 },
                                          overflow: 'hidden',
                                          textOverflow: 'ellipsis',
                                          whiteSpace: 'nowrap',
                                        }}
                                      >
                                        {fileItem.error || 'Failed'}
                                      </Typography>
                                    </Tooltip>
                                  </Box>
                                )}
                                {fileItem.status === 'cancelled' && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <CloseIcon color="disabled" fontSize="small" />
                                    <Typography variant="caption" color="text.secondary">
                                      Cancelled
                                    </Typography>
                                  </Box>
                                )}
                                {fileItem.status === 'uploading' && (
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <CircularProgress size={16} />
                                    <Typography variant="caption" color="text.secondary">
                                      {fileItem.progress || 0}%
                                    </Typography>
                                  </Box>
                                )}
                                {fileItem.status === 'pending' && <Chip size="small" label="Ready" />}
                              </TableCell>
                              <TableCell align="right">
                                {fileItem.status === 'uploading' && (
                                  <Tooltip title="Cancel upload">
                                    <IconButton
                                      onClick={() => cancelFileUpload(fileItem.id)}
                                      size="small"
                                      color="error"
                                    >
                                      <CloseIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                )}
                                {(fileItem.status === 'error' || fileItem.status === 'cancelled') && (
                                  <Tooltip title="Retry this file">
                                    <IconButton
                                      onClick={() => retrySingleFile(fileItem.id)}
                                      disabled={isMultipleUploading}
                                      size="small"
                                      color="primary"
                                    >
                                      <RefreshIcon fontSize="small" />
                                    </IconButton>
                                  </Tooltip>
                                )}
                                <Tooltip title="Remove file">
                                  <IconButton
                                    onClick={() => removeFile(fileItem.id)}
                                    disabled={isMultipleUploading && fileItem.status === 'uploading'}
                                    size="small"
                                  >
                                    <DeleteIcon fontSize="small" />
                                  </IconButton>
                                </Tooltip>
                              </TableCell>
                            </TableRow>
                            {fileItem.status === 'uploading' && (
                              <TableRow>
                                <TableCell colSpan={4} sx={{ py: 0, px: 2 }}>
                                  <LinearProgress
                                    variant="determinate"
                                    value={fileItem.progress || 0}
                                    sx={{ height: 4, borderRadius: 2 }}
                                  />
                                </TableCell>
                              </TableRow>
                            )}
                          </React.Fragment>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  <Button
                    variant="contained"
                    size="large"
                    onClick={handleMultipleUpload}
                    disabled={isMultipleUploading || files.length === 0}
                    startIcon={isMultipleUploading ? undefined : <UploadIcon />}
                    fullWidth
                    sx={{ minHeight: 48 }}
                  >
                    {isMultipleUploading ? 'Uploading...' : `Upload ${files.length} File${files.length !== 1 ? 's' : ''}`}
                  </Button>
                </Box>
              )}
            </Box>
          </Paper>
        )}

        {/* Instructions Section */}
        <Paper elevation={0} sx={{ p: 3, bgcolor: 'action.hover', mt: 3 }}>
          <Typography variant="h6" gutterBottom fontWeight={600}>
            {t('upload.whatHappensNext.title', { defaultValue: 'What happens next?' })}
          </Typography>
          <Typography variant="body2" paragraph>
            {t('upload.whatHappensNext.step1', { defaultValue: 'Your resume will be analyzed using AI technology.' })}
          </Typography>
          <Typography variant="body2" paragraph>
            {t('upload.whatHappensNext.step2', { defaultValue: 'You\'ll receive insights on skills, experience, and recommendations.' })}
          </Typography>
          <Typography variant="body2" paragraph>
            {t('upload.whatHappensNext.step3', { defaultValue: 'View detailed results and download your analysis.' })}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('upload.whatHappensNext.timeline', { defaultValue: 'Analysis typically takes 10-30 seconds.' })}
          </Typography>
        </Paper>
      </Box>
    </ErrorBoundary>
  );
};

export default UnifiedUploadPage;
