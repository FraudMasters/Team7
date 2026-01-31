import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Typography, Box, Paper } from '@mui/material';
import ResumeUploader from '@components/ResumeUploader';

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

  /**
   * Handle successful upload by navigating to results page
   */
  const handleUploadComplete = (resumeId: string) => {
    navigate(`/results/${resumeId}`);
  };

  /**
   * Handle upload errors (could be expanded with error logging/toast)
   */
  const handleUploadError = (error: string) => {
    // Error is displayed in the ResumeUploader component
    // Additional error handling can be added here (e.g., toast notifications)
  };

  return (
    <Box>
      {/* Page Header */}
      <Typography variant="h4" component="h1" gutterBottom fontWeight={600}>
        {t('upload.title')}
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        {t('upload.subtitle')}
      </Typography>

      {/* Upload Component */}
      <Paper elevation={1} sx={{ p: 4, mt: 3 }}>
        <ResumeUploader
          uploadUrl="http://localhost:8000/api/resumes/upload"
          onUploadComplete={handleUploadComplete}
          onUploadError={handleUploadError}
        />
      </Paper>

      {/* Additional Instructions */}
      <Paper elevation={0} sx={{ p: 3, mt: 3, bgcolor: 'action.hover' }}>
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
    </Box>
  );
};

export default UploadPage;
