import React, { useState, useCallback, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Divider,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import {
  Save as SaveIcon,
  Preview as PreviewIcon,
  Refresh as ResetIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { organizationsClient } from '@/api/organizations';
import type { EmailTemplate, EmailTemplateResponse } from '@/types/organization';

/**
 * Template editor state interface
 */
interface EditorState {
  template: EmailTemplate | null;
  loading: boolean;
  saving: boolean;
  previewing: boolean;
  error: string | null;
  success: boolean;
  preview: {
    subject: string;
    body: string;
  } | null;
}

/**
 * Template type definitions with available variables
 */
interface TemplateTypeDefinition {
  type: string;
  label: string;
  description: string;
  variables: Array<{
    name: string;
    description: string;
    example: string;
  }>;
}

/**
 * Available template types
 */
const TEMPLATE_TYPES: TemplateTypeDefinition[] = [
  {
    type: 'candidate_feedback',
    label: 'Candidate Feedback',
    description: 'Notification when candidate feedback is ready',
    variables: [
      { name: '{{candidate_name}}', description: 'Candidate full name', example: 'John Doe' },
      { name: '{{recruiter_name}}', description: 'Recruiter name', example: 'Jane Smith' },
      { name: '{{vacancy_title}}', description: 'Job position title', example: 'Senior Software Engineer' },
      { name: '{{feedback_url}}', description: 'Link to feedback page', example: 'https://app.agenthr.com/feedback/123' },
    ],
  },
  {
    type: 'interview_invitation',
    label: 'Interview Invitation',
    description: 'Invitation to schedule an interview',
    variables: [
      { name: '{{candidate_name}}', description: 'Candidate full name', example: 'John Doe' },
      { name: '{{recruiter_name}}', description: 'Recruiter name', example: 'Jane Smith' },
      { name: '{{vacancy_title}}', description: 'Job position title', example: 'Senior Software Engineer' },
      { name: '{{interview_date}}', description: 'Interview date', example: 'March 15, 2024' },
      { name: '{{interview_time}}', description: 'Interview time', example: '10:00 AM' },
      { name: '{{interview_location}}', description: 'Interview location', example: 'Room 101 or Zoom' },
    ],
  },
  {
    type: 'rejection_notification',
    label: 'Rejection Notification',
    description: 'Notification when candidate is not selected',
    variables: [
      { name: '{{candidate_name}}', description: 'Candidate full name', example: 'John Doe' },
      { name: '{{vacancy_title}}', description: 'Job position title', example: 'Senior Software Engineer' },
      { name: '{{recruiter_name}}', description: 'Recruiter name', example: 'Jane Smith' },
    ],
  },
  {
    type: 'offer_extended',
    label: 'Offer Extended',
    description: 'Notification when job offer is extended',
    variables: [
      { name: '{{candidate_name}}', description: 'Candidate full name', example: 'John Doe' },
      { name: '{{vacancy_title}}', description: 'Job position title', example: 'Senior Software Engineer' },
      { name: '{{recruiter_name}}', description: 'Recruiter name', example: 'Jane Smith' },
      { name: '{{offer_url}}', description: 'Link to offer details', example: 'https://app.agenthr.com/offer/123' },
    ],
  },
  {
    type: 'weekly_digest',
    label: 'Weekly Digest',
    description: 'Weekly summary of recruiting activities',
    variables: [
      { name: '{{recruiter_name}}', description: 'Recruiter name', example: 'Jane Smith' },
      { name: '{{week_start}}', description: 'Start of week date', example: 'March 10, 2024' },
      { name: '{{week_end}}', description: 'End of week date', example: 'March 16, 2024' },
      { name: '{{new_candidates}}', description: 'Number of new candidates', example: '15' },
      { name: '{{interviews_scheduled}}', description: 'Number of interviews scheduled', example: '5' },
    ],
  },
];

/**
 * EmailTemplateEditor Component Props
 */
interface EmailTemplateEditorProps {
  /** Organization ID */
  organizationId: string;
  /** Template ID to edit (optional for creating new template) */
  templateId?: string;
  /** Template type (optional) */
  templateType?: string;
  /** Callback when template is saved successfully */
  onSave?: (template: EmailTemplateResponse) => void;
  /** Callback when error occurs */
  onError?: (error: string) => void;
  /** Read-only mode */
  readOnly?: boolean;
}

/**
 * EmailTemplateEditor Component
 *
 * Provides a comprehensive email template editor with:
 * - Subject and body editing with rich text support
 * - Template type selection with predefined templates
 * - Variable reference guide
 * - Live preview with sample data
 * - Save/update functionality
 * - Form validation
 * - Error handling
 *
 * @example
 * ```tsx
 * <EmailTemplateEditor
 *   organizationId="org-123"
 *   templateType="candidate_feedback"
 *   onSave={(template) => {
 *     // Handle saved template
 *   }}
 * />
 * ```
 */
const EmailTemplateEditor: React.FC<EmailTemplateEditorProps> = ({
  organizationId,
  templateId,
  templateType: initialTemplateType = 'candidate_feedback',
  onSave,
  onError,
  readOnly = false,
}) => {
  const { t } = useTranslation();

  const [state, setState] = useState<EditorState>({
    template: null,
    loading: !!templateId,
    saving: false,
    previewing: false,
    error: null,
    success: false,
    preview: null,
  });

  const [formData, setFormData] = useState({
    template_type: initialTemplateType,
    subject: '',
    body: '',
    is_active: true,
  });

  /**
   * Load template data if templateId is provided
   */
  useEffect(() => {
    const loadTemplate = async () => {
      if (!templateId) return;

      try {
        const template = await organizationsClient.getEmailTemplate(templateId);
        setState((prev) => ({ ...prev, template, loading: false }));
        setFormData({
          template_type: template.template_type,
          subject: template.subject,
          body: template.body,
          is_active: template.is_active,
        });
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : t('errors.failedToLoad');
        setState((prev) => ({
          ...prev,
          error: errorMessage,
          loading: false,
        }));
        onError?.(errorMessage);
      }
    };

    loadTemplate();
  }, [templateId, t, onError]);

  /**
   * Get template type definition
   */
  const getTemplateTypeDefinition = useCallback(
    (type: string): TemplateTypeDefinition | undefined => {
      return TEMPLATE_TYPES.find((tt) => tt.type === type);
    },
    []
  );

  /**
   * Handle form field changes
   */
  const handleFieldChange = useCallback(
    (field: keyof typeof formData) => (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setFormData((prev) => ({
        ...prev,
        [field]: event.target.value,
      }));
      setState((prev) => ({ ...prev, success: false, error: null }));
    },
    []
  );

  /**
   * Handle template type change
   */
  const handleTemplateTypeChange = useCallback((event: React.ChangeEvent<{ value: unknown }>) => {
    const newType = event.target.value as string;
    setFormData((prev) => ({
      ...prev,
      template_type: newType,
    }));
    setState((prev) => ({ ...prev, success: false, error: null }));
  }, []);

  /**
   * Insert variable into body
   */
  const insertVariable = useCallback((variable: string) => {
    setFormData((prev) => ({
      ...prev,
      body: prev.body + variable,
    }));
  }, []);

  /**
   * Preview template with sample data
   */
  const handlePreview = useCallback(async () => {
    setState((prev) => ({ ...prev, previewing: true, error: null }));

    try {
      const templateDef = getTemplateTypeDefinition(formData.template_type);
      if (!templateDef) {
        throw new Error(t('errors.invalidTemplateType') || 'Invalid template type');
      }

      // Build sample variables from template definition
      const variables: Record<string, string> = {};
      templateDef.variables.forEach((v) => {
        const varName = v.name.replace(/{{|}}/g, '');
        variables[varName] = v.example;
      });

      const preview = await organizationsClient.previewEmailTemplate({
        template_id: state.template?.id,
        template_type: formData.template_type,
        variables,
      });

      setState((prev) => ({
        ...prev,
        previewing: false,
        preview: {
          subject: preview.subject,
          body: preview.body,
        },
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : t('errors.failedToPreview');
      setState((prev) => ({
        ...prev,
        previewing: false,
        error: errorMessage,
      }));
      onError?.(errorMessage);
    }
  }, [formData, state.template, getTemplateTypeDefinition, t, onError]);

  /**
   * Reset to original template or defaults
   */
  const handleReset = useCallback(() => {
    if (state.template) {
      setFormData({
        template_type: state.template.template_type,
        subject: state.template.subject,
        body: state.template.body,
        is_active: state.template.is_active,
      });
    } else {
      setFormData({
        template_type: initialTemplateType,
        subject: '',
        body: '',
        is_active: true,
      });
    }
    setState((prev) => ({ ...prev, success: false, error: null, preview: null }));
  }, [state.template, initialTemplateType]);

  /**
   * Validate form
   */
  const validateForm = useCallback((): string | null => {
    if (!formData.subject.trim()) {
      return t('validation.subjectRequired') || 'Subject is required';
    }
    if (!formData.body.trim()) {
      return t('validation.bodyRequired') || 'Body is required';
    }
    return null;
  }, [formData, t]);

  /**
   * Save template
   */
  const handleSave = useCallback(async () => {
    const validationError = validateForm();
    if (validationError) {
      setState((prev) => ({ ...prev, error: validationError }));
      onError?.(validationError);
      return;
    }

    setState((prev) => ({ ...prev, saving: true, error: null }));

    try {
      let savedTemplate: EmailTemplateResponse;

      if (state.template) {
        // Update existing template
        savedTemplate = await organizationsClient.updateEmailTemplate(state.template.id, {
          subject: formData.subject,
          body: formData.body,
          is_active: formData.is_active,
        });
      } else {
        // Create new template
        savedTemplate = await organizationsClient.createEmailTemplate({
          organization_id: organizationId,
          template_type: formData.template_type,
          subject: formData.subject,
          body: formData.body,
          is_active: formData.is_active,
        });
      }

      setState((prev) => ({
        ...prev,
        template: savedTemplate,
        saving: false,
        success: true,
        error: null,
      }));

      onSave?.(savedTemplate);

      // Clear success message after 3 seconds
      setTimeout(() => {
        setState((prev) => ({ ...prev, success: false }));
      }, 3000);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : t('errors.failedToSave');
      setState((prev) => ({
        ...prev,
        saving: false,
        error: errorMessage,
      }));
      onError?.(errorMessage);
    }
  }, [formData, state.template, organizationId, validateForm, onSave, onError, t]);

  const templateDef = getTemplateTypeDefinition(formData.template_type);

  if (state.loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Paper elevation={2} sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" fontWeight={600}>
            {templateId
              ? t('emailTemplates.editTemplate') || 'Edit Email Template'
              : t('emailTemplates.createTemplate') || 'Create Email Template'}
          </Typography>
          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              startIcon={<ResetIcon />}
              onClick={handleReset}
              disabled={readOnly || state.saving}
            >
              {t('common.reset') || 'Reset'}
            </Button>
            <Button
              variant="outlined"
              startIcon={state.previewing ? <CircularProgress size={20} /> : <PreviewIcon />}
              onClick={handlePreview}
              disabled={readOnly || state.previewing || !formData.subject || !formData.body}
            >
              {t('emailTemplates.preview') || 'Preview'}
            </Button>
            {!readOnly && (
              <Button
                variant="contained"
                startIcon={state.saving ? <CircularProgress size={20} /> : <SaveIcon />}
                onClick={handleSave}
                disabled={state.saving}
              >
                {state.saving
                  ? t('common.saving') || 'Saving...'
                  : t('common.save') || 'Save'}
              </Button>
            )}
          </Stack>
        </Box>

        {/* Success Alert */}
        {state.success && (
          <Alert severity="success" icon={<SuccessIcon />} sx={{ mb: 2 }}>
            {t('emailTemplates.saveSuccess') || 'Template saved successfully'}
          </Alert>
        )}

        {/* Error Alert */}
        {state.error && (
          <Alert severity="error" icon={<ErrorIcon />} sx={{ mb: 2 }}>
            {state.error}
          </Alert>
        )}

        {/* Template Type Selection */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth disabled={readOnly || !!state.template}>
              <InputLabel>{t('emailTemplates.templateType') || 'Template Type'}</InputLabel>
              <Select
                value={formData.template_type}
                onChange={handleTemplateTypeChange}
                label={t('emailTemplates.templateType') || 'Template Type'}
              >
                {TEMPLATE_TYPES.map((type) => (
                  <MenuItem key={type.type} value={type.type}>
                    <Box>
                      <Typography variant="body2" fontWeight={500}>
                        {type.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {type.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <Divider sx={{ mb: 3 }} />

        {/* Subject and Body Fields */}
        <Stack spacing={3} sx={{ mb: 3 }}>
          {/* Subject Field */}
          <TextField
            fullWidth
            label={t('emailTemplates.subject') || 'Subject'}
            value={formData.subject}
            onChange={handleFieldChange('subject')}
            disabled={readOnly}
            placeholder={t('emailTemplates.subjectPlaceholder') || 'Enter email subject...'}
            error={!!state.error && !formData.subject.trim()}
            helperText={
              state.error && !formData.subject.trim()
                ? t('validation.subjectRequired')
                : t('emailTemplates.subjectHelp') || 'Use {{variable}} for dynamic content'
            }
            required
          />

          {/* Body Field */}
          <TextField
            fullWidth
            multiline
            rows={12}
            label={t('emailTemplates.body') || 'Body'}
            value={formData.body}
            onChange={handleFieldChange('body')}
            disabled={readOnly}
            placeholder={t('emailTemplates.bodyPlaceholder') || 'Enter email body...'}
            error={!!state.error && !formData.body.trim()}
            helperText={
              state.error && !formData.body.trim()
                ? t('validation.bodyRequired')
                : t('emailTemplates.bodyHelp') || 'Use {{variable}} for dynamic content. HTML is supported.'
            }
            required
          />
        </Stack>

        {/* Variables Reference */}
        {templateDef && (
          <Card elevation={1} sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                {t('emailTemplates.availableVariables') || 'Available Variables'}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {t('emailTemplates.variablesHelp') ||
                  'Click on a variable to insert it into the template body:'}
              </Typography>
              <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
                {templateDef.variables.map((variable) => (
                  <Chip
                    key={variable.name}
                    label={variable.name}
                    onClick={() => !readOnly && insertVariable(variable.name)}
                    disabled={readOnly}
                    sx={{
                      fontFamily: 'monospace',
                      border: '1px solid',
                      borderColor: 'divider',
                      '&:hover': !readOnly
                        ? {
                            bgcolor: 'primary.main',
                            color: 'primary.contrastText',
                          }
                        : {},
                    }}
                  />
                ))}
              </Stack>
              {templateDef.variables.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    {t('emailTemplates.variableDescriptions') || 'Variable Descriptions:'}
                  </Typography>
                  <Grid container spacing={1}>
                    {templateDef.variables.map((variable) => (
                      <Grid item xs={12} sm={6} key={variable.name}>
                        <Box sx={{ p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                          <Typography variant="caption" fontWeight={500} fontFamily="monospace">
                            {variable.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" display="block">
                            {variable.description}
                          </Typography>
                          <Typography variant="caption" color="primary" display="block">
                            {t('emailTemplates.example') || 'Example'}: {variable.example}
                          </Typography>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}
            </CardContent>
          </Card>
        )}

        {/* Preview */}
        {state.preview && (
          <Card elevation={1} sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={600}>
                {t('emailTemplates.preview') || 'Preview'}
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('emailTemplates.subject') || 'Subject'}:
                </Typography>
                <Typography variant="body1">{state.preview.subject}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  {t('emailTemplates.body') || 'Body'}:
                </Typography>
                <Box
                  sx={{
                    p: 2,
                    bgcolor: 'action.hover',
                    borderRadius: 1,
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                  }}
                >
                  {state.preview.body}
                </Box>
              </Box>
            </CardContent>
          </Card>
        )}
      </Paper>
    </Box>
  );
};

export default EmailTemplateEditor;
