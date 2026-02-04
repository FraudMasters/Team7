import React, { useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Typography, Box, Paper, Skeleton, Grid } from '@/components/ui';
import { useEmotionTheme } from '@/contexts/EmotionThemeContext';
import ResumeUploader, { ResumeUploaderHandle } from '@components/ResumeUploader';
import ErrorBoundary from '@components/ErrorBoundary';
import { useKeyboardNavigation } from '@hooks/useKeyboardNavigation';
import ErrorMessage, { ErrorType, ErrorAction } from '@components/ErrorMessage';

/**
 * Upload Page Component
 *
 * Provides the resume upload interface with drag-and-drop support.
 * Users can upload PDF or DOCX resumes for AI-powered analysis.
 *
 * On successful upload, redirects to the results page with the resume ID.
 */
const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const theme = useEmotionTheme();
  const uploaderRef = useRef<ResumeUploaderHandle>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<ErrorType | null>(null);

  /**
   * Detect error type from error message
   */
  const detectUploadErrorType = useCallback((errorMessage: string): ErrorType => {
    const lowerMessage = errorMessage.toLowerCase();

    // File size errors
    if (
      lowerMessage.includes('size') &&
      (lowerMessage.includes('too large') ||
       lowerMessage.includes('exceeded') ||
       lowerMessage.includes('maximum') ||
       lowerMessage.includes('limit'))
    ) {
      return 'fileSizeExceeded';
    }

    // Invalid file format errors
    if (
      lowerMessage.includes('format') ||
      lowerMessage.includes('unsupported') ||
      lowerMessage.includes('extension') ||
      lowerMessage.includes('file type') ||
      lowerMessage.includes('invalid')
    ) {
      return 'invalidFileFormat';
    }

    // Network errors
    if (
      lowerMessage.includes('network') ||
      lowerMessage.includes('connection') ||
      lowerMessage.includes('fetch') ||
      lowerMessage.includes('ERR_NETWORK') ||
      lowerMessage.includes('ERR_INTERNET_DISCONNECTED')
    ) {
      return 'network';
    }

    // Parse errors
    if (
      lowerMessage.includes('parse') ||
      lowerMessage.includes('could not read') ||
      lowerMessage.includes('unable to extract')
    ) {
      return 'resumeParseError';
    }

    // Server errors
    if (
      lowerMessage.includes('server') ||
      lowerMessage.includes('internal') ||
      errorMessage.includes('500') ||
      errorMessage.includes('502') ||
      errorMessage.includes('503')
    ) {
      return 'server';
    }

    // Default to file upload error
    return 'fileUpload';
  }, []);

  /**
   * Handle upload errors with comprehensive error messages
   */
  const handleUploadError = useCallback((error: string) => {
    setUploadError(error);
    setErrorType(detectUploadErrorType(error));
  }, [detectUploadErrorType]);

  /**
   * Retry upload by resetting error and triggering upload again
   */
  const handleRetryUpload = useCallback(() => {
    setUploadError(null);
    setErrorType(null);
    uploaderRef.current?.triggerUpload();
  }, []);

  /**
   * Clear error and reset uploader
   */
  const handleClearError = useCallback(() => {
    setUploadError(null);
    setErrorType(null);
    uploaderRef.current?.cancelUpload();
  }, []);

  /**
   * Get error-specific actions
   */
  const getErrorActions = useCallback((): ErrorAction[] => {
    const actions: ErrorAction[] = [];

    if (errorType === 'fileSizeExceeded' || errorType === 'invalidFileFormat') {
      actions.push({
        label: 'Choose Different File',
        onClick: handleRetryUpload,
        variant: 'contained',
        color: 'primary',
        primary: true,
      });
    } else if (errorType === 'network') {
      actions.push({
        label: 'Retry Upload',
        onClick: handleRetryUpload,
        variant: 'contained',
        color: 'primary',
        primary: true,
      });
    } else {
      actions.push({
        label: 'Try Again',
        onClick: handleRetryUpload,
        variant: 'contained',
        color: 'primary',
        primary: true,
      });
    }

    actions.push({
      label: 'Cancel',
      onClick: handleClearError,
      variant: 'outlined',
      color: 'secondary',
    });

    return actions;
  }, [errorType, handleRetryUpload, handleClearError]);

  /**
   * Keyboard shortcuts for upload page
   */
  const handleTriggerUpload = useCallback(() => {
    uploaderRef.current?.triggerUpload();
  }, []);

  const handleCancelUpload = useCallback(() => {
    uploaderRef.current?.cancelUpload();
  }, []);

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
   * Handle successful upload by navigating to results page
   */
  const handleUploadComplete = useCallback((resumeId: string) => {
    setUploadError(null);
    setErrorType(null);
    navigate(`/results/${resumeId}`);
  }, [navigate]);

  /**
   * Handle uploading state changes
   */
  const handleUploadingChange = (uploading: boolean) => {
    setIsUploading(uploading);
  };

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('Upload page error:', error, errorInfo);
      }}
    >
      <Box sx={{ position: 'relative' }}>
        {/* Loading Skeleton Overlay */}
        {isUploading && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 10,
            bgcolor: alpha(theme.palette.background.paper, 0.95),
            borderRadius: 1,
            p: 0,
          }}
        >
          {/* Page Header Skeleton */}
          <Skeleton
            variant="text"
            width="40%"
            height={48}
            sx={{ mb: 1 }}
            animation="wave"
          />
          <Skeleton
            variant="text"
            width="70%"
            height={24}
            sx={{ mb: 1 }}
            animation="wave"
          />
          <Skeleton
            variant="text"
            width="50%"
            height={20}
            sx={{ mb: 3 }}
            animation="wave"
          />

          {/* Content Grid Skeleton */}
          <Grid container spacing={3}>
            {/* Upload Area Skeleton */}
            <Grid item xs={12} md={7} lg={8}>
              <Box
                sx={{
                  p: 4,
                  border: '2px dashed',
                  borderColor: 'divider',
                  borderRadius: 1,
                  bgcolor: 'background.paper',
                }}
              >
                {/* Upload Icon Skeleton */}
                <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                  <Skeleton
                    variant="circular"
                    width={64}
                    height={64}
                    animation="wave"
                  />
                </Box>

                {/* Title Skeleton */}
                <Skeleton
                  variant="text"
                  width="40%"
                  sx={{ mx: 'auto', mb: 1 }}
                  height={32}
                  animation="wave"
                />

                {/* Subtitle Skeleton */}
                <Skeleton
                  variant="text"
                  width="60%"
                  sx={{ mx: 'auto', mb: 2 }}
                  height={20}
                  animation="wave"
                />

                {/* Chips Skeleton */}
                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', mb: 3 }}>
                  <Skeleton variant="rectangular" width={60} height={32} animation="wave" />
                  <Skeleton variant="rectangular" width={60} height={32} animation="wave" />
                  <Skeleton variant="rectangular" width={100} height={32} animation="wave" />
                </Box>

                {/* Button Skeleton */}
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Skeleton variant="rectangular" width={160} height={40} animation="wave" />
                </Box>
              </Box>
            </Grid2>

            {/* Instructions Section Skeleton */}
            <Grid item xs={12} md={5} lg={4}>
              <Box
                sx={{
                  p: 3,
                  bgcolor: 'action.hover',
                  borderRadius: 1,
                  height: 'fit-content',
                }}
              >
                <Skeleton
                  variant="text"
                  width="50%"
                  height={28}
                  sx={{ mb: 2 }}
                  animation="wave"
                />
                <Skeleton
                  variant="text"
                  width="95%"
                  height={20}
                  sx={{ mb: 1 }}
                  animation="wave"
                />
                <Skeleton
                  variant="text"
                  width="95%"
                  height={20}
                  sx={{ mb: 1 }}
                  animation="wave"
                />
                <Skeleton
                  variant="text"
                  width="95%"
                  height={20}
                  sx={{ mb: 1 }}
                  animation="wave"
                />
                <Skeleton
                  variant="text"
                  width="60%"
                  height={20}
                  animation="wave"
                />
              </Box>
            </Grid2>
          </Grid2>
        </Box>
      )}

      {/* Page Header */}
      <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
        {t('upload.title')}
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        {t('upload.subtitle')}
      </Typography>

      {/* Keyboard Shortcuts Hint */}
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
        <strong>Keyboard shortcuts:</strong> Ctrl+U to upload, Esc to cancel
      </Typography>

      {/* Content Grid - Upload and Instructions */}
      <Grid container spacing={3} sx={{ mt: 0 }}>
        {/* Upload Area */}
        <Grid item xs={12} md={7} lg={8}>
          <Paper elevation={1} sx={{ p: 4 }}>
            {/* Comprehensive Error Message */}
            {uploadError && errorType && (
              <ErrorMessage
                error={errorType}
                message={uploadError}
                actions={getErrorActions()}
                mode="inline"
                showIcon
                severity="error"
              />
            )}

            <ResumeUploader
              ref={uploaderRef}
              uploadUrl="http://localhost:8000/api/resumes/upload"
              onUploadComplete={handleUploadComplete}
              onUploadError={handleUploadError}
              onUploadingChange={handleUploadingChange}
            />
          </Paper>
        </Grid2>

        {/* Instructions Section */}
        <Grid item xs={12} md={5} lg={4}>
          <Paper elevation={0} sx={{ p: 3, bgcolor: 'action.hover' }}>
            <Typography variant="h6" gutterBottom fontWeight={600}>
              {t('upload.whatHappensNext.title')}
            </Typography>
            <Typography variant="body2" paragraph>
              {t('upload.whatHappensNext.step1')}
            </Typography>
            <Typography variant="body2" paragraph>
              {t('upload.whatHappensNext.step2')}
            </Typography>
            <Typography variant="body2" paragraph>
              {t('upload.whatHappensNext.step3')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('upload.whatHappensNext.timeline')}
            </Typography>
          </Paper>
        </Grid2>
      </Grid2>
      </Box>
    </ErrorBoundary>
  );
};

export default UploadPage;
