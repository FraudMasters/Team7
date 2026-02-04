import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Typography, Box, Paper, Stepper, Step, StepLabel } from '@/components/ui';
import ResumeUploader from '@components/ResumeUploader';

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

  /**
   * Handle successful upload by navigating to results page
   */
  const handleUploadComplete = (resumeId: string) => {
    setCurrentStep('complete');
    // Navigate after a brief delay to show the complete step
    setTimeout(() => {
      navigate(`/jobs/resume-results/${resumeId}`);
    }, 1000);
  };

  /**
   * Handle upload errors (could be expanded with error logging/toast)
   */
  const handleUploadError = (error: string) => {
    // Error is displayed in the ResumeUploader component
    // Additional error handling can be added here (e.g., toast notifications)
  };

  /**
   * Handle upload start to update step indicator
   */
  const handleUploadStart = () => {
    setCurrentStep('processing');
  };

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
        <ResumeUploader
          uploadUrl="http://localhost:8000/api/resumes/upload"
          onUploadComplete={handleUploadComplete}
          onUploadError={handleUploadError}
          onUploadStart={handleUploadStart}
        />
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
