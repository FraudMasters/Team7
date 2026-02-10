import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  Alert,
  Stack,
  Divider,
  CircularProgress,
  Grid,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
} from '@mui/material';
import {
  Save as SaveIcon,
  Description as TemplateIcon,
  Palette as PaletteIcon,
  TextFields as FontIcon,
  ViewQuilt as LayoutIcon,
} from '@mui/icons-material';
import { resumeTemplatesClient } from '@/api/resume-templates';
import type { ResumeTemplateResponse, ResumeTemplateUpdate, StyleConfig, LayoutConfig, SectionConfig } from '@/types/resume-templates';
import ColorPicker from '@/components/organizations/ColorPicker';

/**
 * Form state interface
 */
interface TemplateCustomizationFormState {
  name: string;
  description: string;
  primary_color: string;
  secondary_color: string;
  font: string;
  heading_font: string;
  font_size: number;
  margins: string;
  sections: string[];
}

/**
 * Form validation errors interface
 */
interface FormErrors {
  name?: string;
  primary_color?: string;
  secondary_color?: string;
  font?: string;
  heading_font?: string;
  font_size?: string;
  margins?: string;
}

/**
 * Default template customization values
 */
const DEFAULT_CUSTOMIZATION = {
  name: '',
  description: '',
  primary_color: '#2563eb',
  secondary_color: '#64748b',
  font: 'Arial',
  heading_font: 'Arial',
  font_size: 11,
  margins: 'normal',
  sections: ['header', 'experience', 'education', 'skills'],
};

/**
 * Available font options
 */
const FONT_OPTIONS = [
  { value: 'Arial', label: 'Arial' },
  { value: 'Helvetica', label: 'Helvetica' },
  { value: 'Times New Roman', label: 'Times New Roman' },
  { value: 'Georgia', label: 'Georgia' },
  { value: 'Calibri', label: 'Calibri' },
  { value: 'Verdana', label: 'Verdana' },
];

/**
 * Available margin options
 */
const MARGIN_OPTIONS = [
  { value: 'narrow', label: 'Narrow (0.5")' },
  { value: 'normal', label: 'Normal (1")' },
  { value: 'wide', label: 'Wide (1.5")' },
];

/**
 * Available section options
 */
const SECTION_OPTIONS = [
  { value: 'header', label: 'Header' },
  { value: 'experience', label: 'Work Experience' },
  { value: 'education', label: 'Education' },
  { value: 'skills', label: 'Skills' },
  { value: 'projects', label: 'Projects' },
  { value: 'certifications', label: 'Certifications' },
  { value: 'languages', label: 'Languages' },
  { value: 'interests', label: 'Interests' },
];

/**
 * ResumeTemplateCustomizer Component Props
 */
interface ResumeTemplateCustomizerProps {
  /** Template ID to customize */
  templateId: string;
  /** Callback when customization is saved */
  onSave?: (template: ResumeTemplateResponse) => void;
  /** Callback when customization fails */
  onError?: (error: string) => void;
}

/**
 * ResumeTemplateCustomizer Component
 *
 * Provides an interface for customizing resume templates:
 * - Template name and description
 * - Primary and secondary colors
 * - Font family and size
 * - Page margins
 * - Section selection and ordering
 * - Real-time preview of customization changes
 *
 * @example
 * ```tsx
 * <ResumeTemplateCustomizer
 *   templateId="template-123"
 *   onSave={(template) => console.log('Saved:', template.name)}
 *   onError={(error) => console.error('Error:', error)}
 * />
 * ```
 */
const ResumeTemplateCustomizer: React.FC<ResumeTemplateCustomizerProps> = ({
  templateId,
  onSave,
  onError,
}) => {
  const { t } = useTranslation();

  // Form state
  const [formData, setFormData] = useState<TemplateCustomizationFormState>({
    ...DEFAULT_CUSTOMIZATION,
  });

  // UI state
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});
  const [originalTemplate, setOriginalTemplate] = useState<ResumeTemplateResponse | null>(null);

  /**
   * Load template data
   */
  const loadTemplate = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const template = await resumeTemplatesClient.getResumeTemplate(templateId);
      setOriginalTemplate(template);

      setFormData({
        name: template.name,
        description: template.description || '',
        primary_color: template.style_config?.primary_color || DEFAULT_CUSTOMIZATION.primary_color,
        secondary_color: template.style_config?.secondary_color || DEFAULT_CUSTOMIZATION.secondary_color,
        font: template.style_config?.font || DEFAULT_CUSTOMIZATION.font,
        heading_font: template.style_config?.heading_font || DEFAULT_CUSTOMIZATION.heading_font,
        font_size: template.style_config?.font_size || DEFAULT_CUSTOMIZATION.font_size,
        margins: template.layout_config?.margins || DEFAULT_CUSTOMIZATION.margins,
        sections: template.layout_config?.sections || DEFAULT_CUSTOMIZATION.sections,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('resumeTemplate.customizer.errors.loadFailed') || 'Failed to load template';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [templateId, t, onError]);

  /**
   * Validate form fields
   */
  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    // Validate name
    if (!formData.name.trim()) {
      newErrors.name = t('resumeTemplate.customizer.errors.nameRequired') || 'Template name is required';
    }

    // Validate hex color format for all color fields
    const hexColorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;

    if (!hexColorRegex.test(formData.primary_color)) {
      newErrors.primary_color = t('resumeTemplate.customizer.errors.invalidColor') || 'Invalid hex color format (e.g., #2563eb)';
    }

    if (!hexColorRegex.test(formData.secondary_color)) {
      newErrors.secondary_color = t('resumeTemplate.customizer.errors.invalidColor') || 'Invalid hex color format (e.g., #64748b)';
    }

    // Validate fonts
    if (!formData.font.trim()) {
      newErrors.font = t('resumeTemplate.customizer.errors.fontRequired') || 'Font is required';
    }

    if (!formData.heading_font.trim()) {
      newErrors.heading_font = t('resumeTemplate.customizer.errors.headingFontRequired') || 'Heading font is required';
    }

    // Validate font size
    if (formData.font_size < 8 || formData.font_size > 16) {
      newErrors.font_size = t('resumeTemplate.customizer.errors.invalidFontSize') || 'Font size must be between 8 and 16';
    }

    // Validate margins
    if (!formData.margins) {
      newErrors.margins = t('resumeTemplate.customizer.errors.marginsRequired') || 'Margin setting is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData, t]);

  /**
   * Handle text field change
   */
  const handleTextFieldChange = useCallback((field: keyof TemplateCustomizationFormState, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear error for this field when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }

    // Clear success message when user makes changes
    if (successMessage) {
      setSuccessMessage(null);
    }

    // Clear error message when user makes changes
    if (error) {
      setError(null);
    }
  }, [errors, successMessage, error]);

  /**
   * Handle number field change
   */
  const handleNumberFieldChange = useCallback((field: keyof TemplateCustomizationFormState, value: number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }

    if (successMessage) {
      setSuccessMessage(null);
    }

    if (error) {
      setError(null);
    }
  }, [errors, successMessage, error]);

  /**
   * Handle section toggle
   */
  const handleSectionToggle = useCallback((section: string) => {
    setFormData((prev) => ({
      ...prev,
      sections: prev.sections.includes(section)
        ? prev.sections.filter((s) => s !== section)
        : [...prev.sections, section],
    }));

    if (successMessage) {
      setSuccessMessage(null);
    }

    if (error) {
      setError(null);
    }
  }, [successMessage, error]);

  /**
   * Handle form submit
   */
  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();

    // Validate form
    if (!validateForm()) {
      return;
    }

    setSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const updateData: ResumeTemplateUpdate = {
        name: formData.name,
        description: formData.description || undefined,
        style_config: {
          primary_color: formData.primary_color,
          secondary_color: formData.secondary_color,
          font: formData.font,
          heading_font: formData.heading_font,
          font_size: formData.font_size,
        } as StyleConfig,
        layout_config: {
          margins: formData.margins,
          sections: formData.sections,
        } as LayoutConfig,
      };

      const updated = await resumeTemplatesClient.updateResumeTemplate(templateId, updateData);

      setSuccessMessage(t('resumeTemplate.customizer.saveSuccess') || 'Template customization saved successfully');
      setOriginalTemplate(updated);
      onSave?.(updated);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('resumeTemplate.customizer.errors.saveFailed') || 'Failed to save template customization';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setSaving(false);
    }
  }, [formData, templateId, validateForm, t, onSave, onError]);

  /**
   * Handle reset form
   */
  const handleReset = useCallback(() => {
    loadTemplate();
    setSuccessMessage(null);
    setError(null);
    setErrors({});
  }, [loadTemplate]);

  // Load template on mount
  useEffect(() => {
    loadTemplate();
  }, [loadTemplate]);

  /**
   * Calculate contrast color for preview
   */
  const getContrastColor = (hexColor: string): string => {
    const r = parseInt(hexColor.slice(1, 3), 16);
    const g = parseInt(hexColor.slice(3, 5), 16);
    const b = parseInt(hexColor.slice(5, 7), 16);
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    return luminance > 0.5 ? '#000000' : '#FFFFFF';
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {t('resumeTemplate.customizer.title') || 'Customize Template'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('resumeTemplate.customizer.subtitle') || 'Personalize your resume template with colors, fonts, and layout'}
        </Typography>
      </Box>

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error Alert */}
      {error && !loading && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Alert */}
      {successMessage && !loading && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      )}

      {/* Main Content */}
      {!loading && (
        <Grid container spacing={3}>
          {/* Left Column: Form */}
          <Grid item xs={12} md={7}>
            <Paper component="form" onSubmit={handleSubmit} sx={{ p: 4 }}>
              <Stack spacing={4}>
                {/* Template Name */}
                <Box>
                  <TextField
                    fullWidth
                    label={t('resumeTemplate.customizer.templateName') || 'Template Name'}
                    value={formData.name}
                    onChange={(e) => handleTextFieldChange('name', e.target.value)}
                    error={!!errors.name}
                    helperText={errors.name || t('resumeTemplate.customizer.templateNameHelper') || 'A descriptive name for your customized template'}
                    disabled={saving}
                    required
                  />
                </Box>

                <Divider />

                {/* Description */}
                <Box>
                  <TextField
                    fullWidth
                    multiline
                    rows={2}
                    label={t('resumeTemplate.customizer.description') || 'Description'}
                    value={formData.description}
                    onChange={(e) => handleTextFieldChange('description', e.target.value)}
                    helperText={t('resumeTemplate.customizer.descriptionHelper') || 'Optional description of the customization'}
                    disabled={saving}
                  />
                </Box>

                <Divider />

                {/* Primary Color */}
                <Box>
                  <ColorPicker
                    id="primary-color"
                    label={t('resumeTemplate.customizer.primaryColor') || 'Primary Color'}
                    value={formData.primary_color}
                    onChange={(color) => handleTextFieldChange('primary_color', color)}
                    helperText={t('resumeTemplate.customizer.primaryColorHelper') || 'Main color for headings and accents'}
                    defaultColor={DEFAULT_CUSTOMIZATION.primary_color}
                    disabled={saving}
                  />
                </Box>

                <Divider />

                {/* Secondary Color */}
                <Box>
                  <ColorPicker
                    id="secondary-color"
                    label={t('resumeTemplate.customizer.secondaryColor') || 'Secondary Color'}
                    value={formData.secondary_color}
                    onChange={(color) => handleTextFieldChange('secondary_color', color)}
                    helperText={t('resumeTemplate.customizer.secondaryColorHelper') || 'Supporting color for sections and details'}
                    defaultColor={DEFAULT_CUSTOMIZATION.secondary_color}
                    disabled={saving}
                  />
                </Box>

                <Divider />

                {/* Font Family */}
                <Box>
                  <FormControl fullWidth error={!!errors.font}>
                    <InputLabel>
                      {t('resumeTemplate.customizer.font') || 'Font Family'}
                    </Label>
                    <Select
                      value={formData.font}
                      onChange={(e) => handleTextFieldChange('font', e.target.value)}
                      label={t('resumeTemplate.customizer.font') || 'Font Family'}
                      disabled={saving}
                    >
                      {FONT_OPTIONS.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.font && (
                      <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                        {errors.font}
                      </Typography>
                    )}
                  </FormControl>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    {t('resumeTemplate.customizer.fontHelper') || 'Main font for body text'}
                  </Typography>
                </Box>

                <Divider />

                {/* Heading Font */}
                <Box>
                  <FormControl fullWidth error={!!errors.heading_font}>
                    <InputLabel>
                      {t('resumeTemplate.customizer.headingFont') || 'Heading Font'}
                    </InputLabel>
                    <Select
                      value={formData.heading_font}
                      onChange={(e) => handleTextFieldChange('heading_font', e.target.value)}
                      label={t('resumeTemplate.customizer.headingFont') || 'Heading Font'}
                      disabled={saving}
                    >
                      {FONT_OPTIONS.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.heading_font && (
                      <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                        {errors.heading_font}
                      </Typography>
                    )}
                  </FormControl>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    {t('resumeTemplate.customizer.headingFontHelper') || 'Font for section headings and titles'}
                  </Typography>
                </Box>

                <Divider />

                {/* Font Size */}
                <Box>
                  <TextField
                    fullWidth
                    type="number"
                    label={t('resumeTemplate.customizer.fontSize') || 'Font Size (pt)'}
                    value={formData.font_size}
                    onChange={(e) => handleNumberFieldChange('font_size', parseInt(e.target.value) || DEFAULT_CUSTOMIZATION.font_size)}
                    error={!!errors.font_size}
                    helperText={errors.font_size || t('resumeTemplate.customizer.fontSizeHelper') || 'Base font size in points (8-16)'}
                    disabled={saving}
                    inputProps={{ min: 8, max: 16, step: 1 }}
                  />
                </Box>

                <Divider />

                {/* Margins */}
                <Box>
                  <FormControl fullWidth error={!!errors.margins}>
                    <InputLabel>
                      {t('resumeTemplate.customizer.margins') || 'Page Margins'}
                    </InputLabel>
                    <Select
                      value={formData.margins}
                      onChange={(e) => handleTextFieldChange('margins', e.target.value)}
                      label={t('resumeTemplate.customizer.margins') || 'Page Margins'}
                      disabled={saving}
                    >
                      {MARGIN_OPTIONS.map((option) => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                    {errors.margins && (
                      <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                        {errors.margins}
                      </Typography>
                    )}
                  </FormControl>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    {t('resumeTemplate.customizer.marginsHelper') || 'Margin size for the page layout'}
                  </Typography>
                </Box>

                <Divider />

                {/* Sections */}
                <Box>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    {t('resumeTemplate.customizer.sections') || 'Include Sections'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {t('resumeTemplate.customizer.sectionsHelper') || 'Select which sections to include in your resume'}
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {SECTION_OPTIONS.map((section) => (
                      <Chip
                        key={section.value}
                        label={section.label}
                        onClick={() => handleSectionToggle(section.value)}
                        color={formData.sections.includes(section.value) ? 'primary' : 'default'}
                        variant={formData.sections.includes(section.value) ? 'filled' : 'outlined'}
                        disabled={saving}
                        clickable
                      />
                    ))}
                  </Box>
                </Box>

                <Divider />

                {/* Action Buttons */}
                <Stack direction="row" spacing={2} justifyContent="flex-end">
                  <Button
                    type="button"
                    variant="outlined"
                    onClick={handleReset}
                    disabled={saving}
                    size="large"
                  >
                    {t('common.reset') || 'Reset'}
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                    disabled={saving}
                    size="large"
                  >
                    {saving ? (t('common.saving') || 'Saving...') : (t('common.save') || 'Save Changes')}
                  </Button>
                </Stack>
              </Stack>
            </Paper>
          </Grid>

          {/* Right Column: Preview */}
          <Grid item xs={12} md={5}>
            <Paper sx={{ p: 4, position: 'sticky', top: 20 }}>
              <Stack spacing={3}>
                {/* Preview Header */}
                <Box>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    {t('resumeTemplate.customizer.preview.title') || 'Live Preview'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('resumeTemplate.customizer.preview.subtitle') || 'See how your customization will look'}
                  </Typography>
                </Box>

                <Divider />

                {/* Preview Components */}
                <Stack spacing={2}>
                  {/* Template Icon */}
                  <Box
                    sx={{
                      p: 2,
                      bgcolor: 'background.default',
                      borderRadius: 2,
                      textAlign: 'center',
                    }}
                  >
                    <TemplateIcon
                      sx={{
                        fontSize: 48,
                        color: formData.primary_color,
                      }}
                    />
                  </Box>

                  {/* Heading Preview */}
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      {t('resumeTemplate.customizer.preview.heading') || 'Heading Style'}
                    </Typography>
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 1,
                        bgcolor: 'background.default',
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Typography
                        variant="h6"
                        sx={{
                          color: formData.primary_color,
                          fontFamily: formData.heading_font,
                        }}
                      >
                        {t('resumeTemplate.customizer.preview.headingText') || 'John Doe'}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Body Text Preview */}
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      {t('resumeTemplate.customizer.preview.bodyText') || 'Body Text Style'}
                    </Typography>
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 1,
                        bgcolor: 'background.default',
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Typography
                        variant="body2"
                        sx={{
                          color: 'text.primary',
                          fontFamily: formData.font,
                          fontSize: `${formData.font_size}pt`,
                        }}
                      >
                        {t('resumeTemplate.customizer.preview.bodyTextSample') || 'Professional with 5+ years of experience in software development...'}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Color Preview */}
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      {t('resumeTemplate.customizer.preview.colors') || 'Color Scheme'}
                    </Typography>
                    <Stack direction="row" spacing={1}>
                      <Box
                        sx={{
                          flex: 1,
                          p: 2,
                          borderRadius: 1,
                          bgcolor: formData.primary_color,
                          color: getContrastColor(formData.primary_color),
                          textAlign: 'center',
                          fontWeight: 600,
                        }}
                      >
                        {t('resumeTemplate.customizer.preview.primary') || 'Primary'}
                      </Box>
                      <Box
                        sx={{
                          flex: 1,
                          p: 2,
                          borderRadius: 1,
                          bgcolor: formData.secondary_color,
                          color: getContrastColor(formData.secondary_color),
                          textAlign: 'center',
                          fontWeight: 600,
                        }}
                      >
                        {t('resumeTemplate.customizer.preview.secondary') || 'Secondary'}
                      </Box>
                    </Stack>
                  </Box>

                  {/* Sections Preview */}
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      {t('resumeTemplate.customizer.preview.sections') || 'Sections'}
                    </Typography>
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 1,
                        bgcolor: 'background.default',
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {formData.sections.map((section) => (
                          <Chip
                            key={section}
                            label={t(`resumeTemplate.sections.${section}`, section)}
                            size="small"
                            variant="outlined"
                            sx={{
                              borderColor: formData.secondary_color,
                              color: formData.secondary_color,
                            }}
                          />
                        ))}
                      </Box>
                    </Box>
                  </Box>
                </Stack>

                <Divider />

                {/* Info Box */}
                <Box sx={{ p: 2, bgcolor: 'info.main', bgcolorOpacity: 0.1, borderRadius: 2 }}>
                  <Stack direction="row" spacing={2} alignItems="flex-start">
                    <PaletteIcon color="info" sx={{ fontSize: 20 }} />
                    <Box>
                      <Typography variant="caption" fontWeight={600} color="info.dark">
                        {t('resumeTemplate.customizer.preview.infoTitle') || 'Preview'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {t('resumeTemplate.customizer.preview.infoHelper') || 'Changes are reflected in real-time above'}
                      </Typography>
                    </Box>
                  </Stack>
                </Box>
              </Stack>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default ResumeTemplateCustomizer;
