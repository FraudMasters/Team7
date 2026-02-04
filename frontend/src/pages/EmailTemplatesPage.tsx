import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Container,
  Typography,
  Paper,
  Stack,
  Breadcrumbs,
  Link,
  Alert,
  AlertTitle,
} from '@mui/material';
import {
  Home as HomeIcon,
  Mail as MailIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import EmailTemplateEditor from '@/components/organizations/EmailTemplateEditor';

/**
 * Email Templates Page
 *
 * Provides a UI for managing email templates for the organization.
 * Users can create and edit email templates with variable substitution.
 */
const EmailTemplatesPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // For this demo, we use a hardcoded organization ID
  // In a real application, this would come from authentication context
  const organizationId = 'demo-org-123';

  /**
   * Handle successful template save
   */
  const handleSave = (template: any) => {
    // Template saved successfully - callback for parent components
  };

  /**
   * Handle error during save
   */
  const handleError = (error: string) => {
    // Error handling - display error in UI
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs
        sx={{ mb: 3 }}
        separator="›"
        aria-label="breadcrumb"
      >
        <Link
          underline="hover"
          color="inherit"
          sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
          {t('common.home') || 'Home'}
        </Link>
        <Link
          underline="hover"
          color="inherit"
          sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
          onClick={() => navigate('/recruiter/dashboard')}
        >
          <SettingsIcon sx={{ mr: 0.5 }} fontSize="inherit" />
          {t('common.settings') || 'Settings'}
        </Link>
        <Typography
          sx={{ display: 'flex', alignItems: 'center' }}
          color="text.primary"
        >
          <MailIcon sx={{ mr: 0.5 }} fontSize="inherit" />
          {t('emailTemplates.pageTitle') || 'Email Templates'}
        </Typography>
      </Breadcrumbs>

      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {t('emailTemplates.pageTitle') || 'Email Templates'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('emailTemplates.pageDescription') ||
            'Create and customize email templates for different notifications. Use variables to personalize your emails.'}
        </Typography>
      </Box>

      {/* Info Alert */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>{t('emailTemplates.infoTitle') || 'How it works'}</AlertTitle>
        <Typography variant="body2">
          {t('emailTemplates.infoMessage') ||
            'Email templates allow you to customize the content of notifications sent to recruiters and candidates. Click on variables like {{candidate_name}} to insert them into your template. Preview your template before saving to see how it will look with sample data.'}
        </Typography>
      </Alert>

      {/* Email Template Editor */}
      <Paper elevation={2}>
        <EmailTemplateEditor
          organizationId={organizationId}
          templateType="candidate_feedback"
          onSave={handleSave}
          onError={handleError}
        />
      </Paper>

      {/* Additional Help */}
      <Box sx={{ mt: 4 }}>
        <Paper
          elevation={1}
          sx={{
            p: 3,
            bgcolor: 'info.50',
            border: '1px solid',
            borderColor: 'info.200',
          }}
        >
          <Typography variant="h6" gutterBottom fontWeight={600}>
            {t('emailTemplates.availableTemplateTypes') || 'Available Template Types'}
          </Typography>
          <Stack spacing={1}>
            <Typography variant="body2" component="div">
              <strong>{t('emailTemplateTypes.candidate_feedback') || 'Candidate Feedback'}</strong> - {t('emailTemplateTypes.candidate_feedback_desc') || 'Notification when candidate feedback is ready'}
            </Typography>
            <Typography variant="body2" component="div">
              <strong>{t('emailTemplateTypes.interview_invitation') || 'Interview Invitation'}</strong> - {t('emailTemplateTypes.interview_invitation_desc') || 'Invitation to schedule an interview'}
            </Typography>
            <Typography variant="body2" component="div">
              <strong>{t('emailTemplateTypes.rejection_notification') || 'Rejection Notification'}</strong> - {t('emailTemplateTypes.rejection_notification_desc') || 'Notification when candidate is not selected'}
            </Typography>
            <Typography variant="body2" component="div">
              <strong>{t('emailTemplateTypes.offer_extended') || 'Offer Extended'}</strong> - {t('emailTemplateTypes.offer_extended_desc') || 'Notification when job offer is extended'}
            </Typography>
            <Typography variant="body2" component="div">
              <strong>{t('emailTemplateTypes.weekly_digest') || 'Weekly Digest'}</strong> - {t('emailTemplateTypes.weekly_digest_desc') || 'Weekly summary of recruiting activities'}
            </Typography>
          </Stack>
        </Paper>
      </Box>
    </Container>
  );
};

export default EmailTemplatesPage;
