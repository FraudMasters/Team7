import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Typography, Box, Paper, Stepper, Step, StepLabel } from '@mui/material';
import { config } from '@/config';
import ResumeUploader from '@components/ResumeUploader';
import ProcessingProgressIndicator, {
  ProcessingProgressIndicatorHandle,
} from '@components/ProcessingProgressIndicator';
import { useWebSocket } from '@/hooks/useWebSocket';
import type {
  ResumeProgressStage,
  ResumeProcessingState,
} from '@/types/resume-progress';

/**
 * Upload workflow step
 */
type UploadStep = 'upload' | 'processing' | 'complete';

/**
 * Resume Upload Page Component
 *
 * Provides the resume upload interface for candidates with drag-and-drop support.
 * Features a streamlined 3-step workflow:
 * 1. Upload Resume - Select or drag-drop resume file
 * 2. Processing - AI analyzes the resume
 * 3. View Results - See analysis and rankings
 *
 * On successful upload, redirects to the results page with the resume ID.
 */
const ResumeUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const [currentStep, setCurrentStep] = useState<UploadStep>('upload');
  const [currentResumeId, setCurrentResumeId] = useState<string | null>(null);

  // Processing progress state
  const [processingStage, setProcessingStage] = useState<ResumeProgressStage>('parsing');
  const [processingProgress, setProcessingProgress] = useState<number>(0);
  const [processingMessage, setProcessingMessage] = useState<string>('');
  const [isProcessingComplete, setIsProcessingComplete] = useState<boolean>(false);
  const [hasProcessingError, setHasProcessingError] = useState<boolean>(false);
  const [processingError, setProcessingError] = useState<string>('');

  // Progress indicator ref for programmatic control
  const progressIndicatorRef = useRef<ProcessingProgressIndicatorHandle>(null);

  /**
   * Get current user ID from localStorage or use a default
   * In a real app, this would come from the auth context
   */
  const getCurrentUserId = useCallback((): string => {
    return 'guest-user'; // Default user ID for resume upload
  }, []);

  /**
   * WebSocket connection for real-time progress updates
   */
  const { isConnected } = useWebSocket({
    userId: getCurrentUserId(),
    onMessage: useCallback((message) => {
      // Handle resume progress messages from WebSocket
      if (message.type === 'resume_progress' || message.type === 'batch_progress') {
        const progressMessage = message as any;
        if (progressMessage.stage) {
          setProcessingStage(progressMessage.stage);
          setProcessingProgress(progressMessage.progress || 0);
          setProcessingMessage(progressMessage.message || '');

          // Update progress indicator via ref if available
          if (progressIndicatorRef.current) {
            if (progressMessage.stage === 'complete') {
              progressIndicatorRef.current.setComplete(progressMessage.message);
            } else if (progressMessage.stage === 'failed') {
              progressIndicatorRef.current.setError(
                progressMessage.error_message || 'Processing failed'
              );
            } else {
              progressIndicatorRef.current.updateProgress({
                stage: progressMessage.stage,
                progress: progressMessage.progress,
                message: progressMessage.message,
              });
            }
          }
        }

        // Handle completion
        if (progressMessage.stage === 'complete') {
          setIsProcessingComplete(true);
          setHasProcessingError(false);
        }

        // Handle errors
        if (progressMessage.stage === 'failed') {
          setIsProcessingComplete(false);
          setHasProcessingError(true);
          setProcessingError(progressMessage.error_message || 'Processing failed');
        }
      }
    }, []),
    onError: useCallback((error) => {
      // Handle WebSocket errors without stopping the upload
      // The upload will still complete, we just won't get real-time updates
    }, []),
  });

  /**
   * Handle successful upload by navigating to results page
   */
  const handleUploadComplete = (resumeId: string) => {
    setCurrentResumeId(resumeId);
    // Stay on processing step to show progress
    // Will navigate after processing completes or timeout
    setTimeout(() => {
      if (!isProcessingComplete) {
        // If processing not complete after timeout, still navigate
        navigate(`/jobs/resume-results/${resumeId}`);
      }
    }, 5000); // 5 second timeout
  };

  /**
   * Handle upload errors (could be expanded with error logging/toast)
   */
  const handleUploadError = (error: string) => {
    // Error is displayed in the ResumeUploader component
    // Additional error handling can be added here (e.g., toast notifications)
  };

  /**
   * Handle upload start to update step indicator and reset progress state
   */
  const handleUploadStart = () => {
    setCurrentStep('processing');
    // Reset progress state for new upload
    setProcessingStage('parsing');
    setProcessingProgress(0);
    setProcessingMessage('');
    setIsProcessingComplete(false);
    setHasProcessingError(false);
    setProcessingError('');
    // Reset progress indicator
    progressIndicatorRef.current?.reset();
  };

  /**
   * Navigate to results when processing is complete
   */
  useEffect(() => {
    if (isProcessingComplete && currentResumeId) {
      const timeoutId = setTimeout(() => {
        navigate(`/jobs/resume-results/${currentResumeId}`);
      }, 1500); // Brief delay to show completion state

      return () => clearTimeout(timeoutId);
    }
  }, [isProcessingComplete, currentResumeId, navigate]);

  // Define workflow steps
  const steps = [
    { label: t('upload.steps.upload'), key: 'upload' },
    { label: t('upload.steps.processing'), key: 'processing' },
    { label: t('upload.steps.results'), key: 'complete' },
  ];

  // Calculate active step index
  const activeStep = steps.findIndex((step) => step.key === currentStep);

  return (
    <Box>
      {/* Page Header */}
      <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
        {t('upload.title')}
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        {t('upload.subtitle')}
      </Typography>

      {/* Step Progress Indicator */}
      <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={activeStep} alternativeLabel>
          {steps.map((step) => (
            <Step key={step.key}>
              <StepLabel>{step.label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Upload Component */}
      <Paper elevation={1} sx={{ p: 4 }}>
        {currentStep === 'upload' && (
          <ResumeUploader
            uploadUrl={`${config.api.url}/api/resumes/upload`}
            onUploadComplete={handleUploadComplete}
            onUploadError={handleUploadError}
            onUploadStart={handleUploadStart}
          />
        )}

        {/* Processing Progress Indicator */}
        {currentStep === 'processing' && (
          <ProcessingProgressIndicator
            ref={progressIndicatorRef}
            stage={processingStage}
            progress={processingProgress}
            message={processingMessage}
            isComplete={isProcessingComplete}
            hasError={hasProcessingError}
            error={processingError}
            resumeId={currentResumeId || undefined}
            showStepper={true}
            title={t('upload.processingTitle')}
            size="large"
          />
        )}
      </Paper>

      {/* Quick Info - Streamlined from full instructions */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            flex: '1 1 200px',
            bgcolor: 'action.hover',
            borderLeft: 4,
            borderColor: 'primary.main',
          }}
        >
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            {t('upload.info.acceptedFormats')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            PDF, DOCX (Max 10MB)
          </Typography>
        </Paper>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            flex: '1 1 200px',
            bgcolor: 'action.hover',
            borderLeft: 4,
            borderColor: 'success.main',
          }}
        >
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            {t('upload.info.processingTime')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('upload.whatHappensNext.timeline')}
          </Typography>
        </Paper>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            flex: '1 1 200px',
            bgcolor: 'action.hover',
            borderLeft: 4,
            borderColor: 'info.main',
          }}
        >
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            {t('upload.info.whatsNext')}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t('upload.info.viewResults')}
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
};

export default ResumeUploadPage;
export { ResumeUploadPage };
