import React, { useState, useCallback, useRef, forwardRef, useImperativeHandle, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Stack,
  Card,
  CardContent,
  Chip,
  Grid,
} from '@mui/material';
import {
  Description as TemplateIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Visibility as PreviewIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { resumeTemplatesClient } from '@/api/resume-templates';
import type { ResumeTemplateResponse } from '@/types/resume-templates';

/**
 * Preview state interface
 */
interface PreviewState {
  loading: boolean;
  error: string | null;
  template: ResumeTemplateResponse | null;
}

/**
 * Imperative handle exposed by ResumeTemplatePreview
 */
export interface ResumeTemplatePreviewHandle {
  /**
   * Refresh the template preview
   */
  refreshPreview: () => void;
  /**
   * Reset the preview to initial state
   */
  resetPreview: () => void;
  /**
   * Get current template data
   */
  getTemplate: () => ResumeTemplateResponse | null;
}

/**
 * ResumeTemplatePreview Component Props
 */
interface ResumeTemplatePreviewProps {
  /** Template ID to preview */
  templateId: string;
  /** Callback when preview loads successfully */
  onPreviewLoad?: (template: ResumeTemplateResponse) => void;
  /** Callback when preview fails to load */
  onPreviewError?: (error: string) => void;
  /** Callback when loading state changes */
  onLoadingChange?: (isLoading: boolean) => void;
  /** Show download button */
  showDownloadButton?: boolean;
  /** Show preview button */
  showPreviewButton?: boolean;
  /** Custom action buttons */
  customActions?: React.ReactNode;
}

/**
 * ResumeTemplatePreview Component
 *
 * Displays a preview of a resume template with:
 * - Template metadata (name, description, type)
 * - Style configuration (colors, fonts)
 * - Layout configuration (sections, margins)
 * - ATS compliance badge
 * - Error handling and display
 * - Loading and success states
 *
 * @example
 * ```tsx
 * const previewRef = useRef<ResumeTemplatePreviewHandle>(null);
 * <ResumeTemplatePreview
 *   ref={previewRef}
 *   templateId="template-123"
 *   onPreviewLoad={(template) => console.log('Loaded:', template.name)}
 *   showDownloadButton={true}
 * />
 *
 * // Programmatic control
 * previewRef.current?.refreshPreview();
 * previewRef.current?.resetPreview();
 * const template = previewRef.current?.getTemplate();
 * ```
 */
const ResumeTemplatePreview = forwardRef<ResumeTemplatePreviewHandle, ResumeTemplatePreviewProps>(({
  templateId,
  onPreviewLoad,
  onPreviewError,
  onLoadingChange,
  showDownloadButton = true,
  showPreviewButton = true,
  customActions,
}, ref) => {
  const { t } = useTranslation();

  const [previewState, setPreviewState] = useState<PreviewState>({
    loading: false,
    error: null,
    template: null,
  });

  /**
   * Notify parent of loading state changes
   */
  useEffect(() => {
    onLoadingChange?.(previewState.loading);
  }, [previewState.loading, onLoadingChange]);

  /**
   * Reset preview state
   */
  const handleReset = useCallback(() => {
    setPreviewState({
      loading: false,
      error: null,
      template: null,
    });
  }, []);

  /**
   * Expose methods via ref for parent component access
   */
  useImperativeHandle(ref, () => ({
    refreshPreview: () => {
      fetchTemplate();
    },
    resetPreview: () => {
      handleReset();
    },
    getTemplate: () => {
      return previewState.template;
    },
  }), [previewState.template, handleReset]);

  /**
   * Fetch template data from API
   */
  const fetchTemplate = useCallback(async () => {
    if (!templateId) {
      setPreviewState((prev) => ({
        ...prev,
        error: t('resumeTemplate.preview.errors.noTemplateId'),
      }));
      onPreviewError?.(t('resumeTemplate.preview.errors.noTemplateId'));
      return;
    }

    setPreviewState((prev) => ({
      ...prev,
      loading: true,
      error: null,
    }));

    try {
      const template = await resumeTemplatesClient.getResumeTemplate(templateId);

      setPreviewState({
        loading: false,
        error: null,
        template,
      });

      onPreviewLoad?.(template);
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : t('resumeTemplate.preview.errors.loadFailed');

      setPreviewState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));

      onPreviewError?.(errorMessage);
    }
  }, [templateId, onPreviewLoad, onPreviewError, t]);

  /**
   * Fetch template on mount or when templateId changes
   */
  useEffect(() => {
    fetchTemplate();
  }, [fetchTemplate]);

  /**
   * Handle download button click
   */
  const handleDownload = useCallback(() => {
    if (!previewState.template) return;

    // TODO: Implement PDF download functionality
    // This will be handled by the PDF generator service
    console.log('Download template:', previewState.template.id);
  }, [previewState.template]);

  /**
   * Render loading state
   */
  if (previewState.loading && !previewState.template) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          py: 8,
        }}
      >
        <CircularProgress size={60} sx={{ mb: 3 }} />
        <Typography variant="h6" color="text.secondary">
          {t('resumeTemplate.preview.loading')}
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (previewState.error && !previewState.template) {
    return (
      <Paper
        elevation={2}
        sx={{
          p: 4,
          border: '2px solid',
          borderColor: 'error.main',
          bgcolor: 'error.main',
        }}
      >
        <Alert
          severity="error"
          icon={<ErrorIcon />}
          action={
            <Button
              color="inherit"
              size="small"
              onClick={fetchTemplate}
              startIcon={<RefreshIcon />}
              disabled={previewState.loading}
            >
              {t('common.retry')}
            </Button>
          }
        >
          {previewState.error}
        </Alert>
      </Paper>
    );
  }

  /**
   * Render empty state
   */
  if (!previewState.template) {
    return (
      <Paper
        elevation={1}
        sx={{
          p: 4,
          textAlign: 'center',
        }}
      >
        <TemplateIcon
          sx={{
            fontSize: 64,
            color: 'text.disabled',
            mb: 2,
          }}
        />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          {t('resumeTemplate.preview.noTemplate')}
        </Typography>
      </Paper>
    );
  }

  const { template } = previewState;

  /**
   * Get template type label color
   */
  const getTypeColor = (type: string): 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning' => {
    const colorMap: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning'> = {
      modern: 'primary',
      classic: 'secondary',
      creative: 'secondary',
      ats_friendly: 'success',
      professional: 'info',
      minimal: 'default',
      elegant: 'secondary',
      bold: 'warning',
    };
    return colorMap[type] || 'default';
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper
        elevation={2}
        sx={{
          p: 4,
          border: '2px solid',
          borderColor: previewState.error
            ? 'error.main'
            : 'divider',
          bgcolor: 'background.paper',
          transition: 'all 0.2s ease-in-out',
        }}
      >
        {/* Error Alert (non-blocking) */}
        {previewState.error && template && (
          <Alert
            severity="warning"
            icon={<ErrorIcon />}
            sx={{ mb: 2 }}
            onClose={() => setPreviewState((prev) => ({ ...prev, error: null }))}
          >
            {previewState.error}
          </Alert>
        )}

        {/* Template Header */}
        <Box sx={{ mb: 3 }}>
          {/* Title Row */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ flex: 1 }}>
              {/* Template Name */}
              <Typography variant="h5" fontWeight={600} gutterBottom>
                {template.name}
              </Typography>

              {/* Template Type */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <Chip
                  label={t(`resumeTemplate.types.${template.template_type}`, template.template_type)}
                  size="small"
                  color={getTypeColor(template.template_type)}
                  variant="outlined"
                />
                {template.is_default && (
                  <Chip
                    label={t('resumeTemplate.default')}
                    size="small"
                    color="primary"
                    variant="filled"
                  />
                )}
                {template.is_ats_compliant && (
                  <Chip
                    label={t('resumeTemplate.atsCompliant')}
                    size="small"
                    color="success"
                    variant="outlined"
                    icon={<SuccessIcon sx={{ fontSize: 16 }} />}
                  />
                )}
              </Box>
            </Box>

            {/* Action Buttons */}
            <Stack direction="row" spacing={1}>
              {showPreviewButton && (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<PreviewIcon />}
                  disabled={previewState.loading}
                >
                  {t('resumeTemplate.preview.preview')}
                </Button>
              )}
              {showDownloadButton && (
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<DownloadIcon />}
                  onClick={handleDownload}
                  disabled={previewState.loading}
                >
                  {t('resumeTemplate.preview.download')}
                </Button>
              )}
              {customActions}
            </Stack>
          </Box>

          {/* Description */}
          {template.description && (
            <Typography variant="body2" color="text.secondary">
              {template.description}
            </Typography>
          )}
        </Box>

        {/* Template Configuration */}
        <Grid container spacing={2}>
          {/* Style Configuration */}
          {template.style_config && (
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    {t('resumeTemplate.preview.styleConfig')}
                  </Typography>
                  <Stack spacing={1}>
                    {template.style_config.primary_color && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box
                          sx={{
                            width: 24,
                            height: 24,
                            bgcolor: template.style_config.primary_color,
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1,
                          }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {t('resumeTemplate.preview.primaryColor')}: {template.style_config.primary_color}
                        </Typography>
                      </Box>
                    )}
                    {template.style_config.font && (
                      <Typography variant="body2" color="text.secondary">
                        {t('resumeTemplate.preview.font')}: {template.style_config.font}
                      </Typography>
                    )}
                    {template.style_config.font_size && (
                      <Typography variant="body2" color="text.secondary">
                        {t('resumeTemplate.preview.fontSize')}: {template.style_config.font_size}pt
                      </Typography>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Layout Configuration */}
          {template.layout_config && (
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                    {t('resumeTemplate.preview.layoutConfig')}
                  </Typography>
                  <Stack spacing={1}>
                    {template.layout_config.margins && (
                      <Typography variant="body2" color="text.secondary">
                        {t('resumeTemplate.preview.margins')}: {t(`resumeTemplate.margins.${template.layout_config.margins}`, template.layout_config.margins)}
                      </Typography>
                    )}
                    {template.layout_config.sections && template.layout_config.sections.length > 0 && (
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {t('resumeTemplate.preview.sections')}:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {template.layout_config.sections.map((section) => (
                            <Chip
                              key={section}
                              label={t(`resumeTemplate.sections.${section}`, section)}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      </Box>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>

        {/* Refresh Button */}
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            size="small"
            onClick={fetchTemplate}
            startIcon={previewState.loading ? <CircularProgress size={16} /> : <RefreshIcon />}
            disabled={previewState.loading}
          >
            {t('resumeTemplate.preview.refresh')}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
});

ResumeTemplatePreview.displayName = 'ResumeTemplatePreview';

export default ResumeTemplatePreview;
