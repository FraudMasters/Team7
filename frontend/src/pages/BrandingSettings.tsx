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
} from '@mui/material';
import {
  Save as SaveIcon,
  Palette as PaletteIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { organizationsClient } from '@/api/organizations';
import type { BrandingSettingsResponse, BrandingSettingsUpdate } from '@/types';
import LogoUpload from '@/components/organizations/LogoUpload';
import ColorPicker from '@/components/organizations/ColorPicker';

/**
 * Form state interface
 */
interface BrandingFormState {
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  background_color: string;
  text_color: string;
  logo_url: string | null;
  favicon_url: string;
}

/**
 * Form validation errors interface
 */
interface FormErrors {
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  background_color?: string;
  text_color?: string;
  logo_url?: string;
  favicon_url?: string;
}

/**
 * Default branding colors
 */
const DEFAULT_COLORS = {
  primary_color: '#3B82F6',
  secondary_color: '#10B981',
  accent_color: '#F59E0B',
  background_color: '#FFFFFF',
  text_color: '#1F2937',
};

/**
 * Branding Settings Page
 *
 * Provides an interface for managing organization branding:
 * - Primary, secondary, and accent colors
 * - Logo upload
 * - Background and text colors
 * - Real-time preview of branding changes
 *
 * Accessible at /branding-settings
 *
 * @example
 * ```tsx
 * // Route configuration in App.tsx
 * <Route path="/branding-settings" element={<BrandingSettings />} />
 * ```
 */
const BrandingSettings: React.FC = () => {
  const { t } = useTranslation();

  // Form state
  const [organizationId, setOrganizationId] = useState<string>('org123'); // In production, from auth context
  const [brandingId, setBrandingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<BrandingFormState>({
    primary_color: DEFAULT_COLORS.primary_color,
    secondary_color: DEFAULT_COLORS.secondary_color,
    accent_color: DEFAULT_COLORS.accent_color,
    background_color: DEFAULT_COLORS.background_color,
    text_color: DEFAULT_COLORS.text_color,
    logo_url: null,
    favicon_url: '',
  });

  // UI state
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});

  /**
   * Load branding settings
   */
  const loadBrandingSettings = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // First, try to get existing branding settings for this organization
      const response = await organizationsClient.listBrandingSettings(organizationId);

      if (response.branding_settings && response.branding_settings.length > 0) {
        // Use the first (and typically only) branding settings for this org
        const branding = response.branding_settings[0];
        setBrandingId(branding.id);
        setFormData({
          primary_color: branding.primary_color || DEFAULT_COLORS.primary_color,
          secondary_color: branding.secondary_color || DEFAULT_COLORS.secondary_color,
          accent_color: branding.accent_color || DEFAULT_COLORS.accent_color,
          background_color: branding.background_color || DEFAULT_COLORS.background_color,
          text_color: branding.text_color || DEFAULT_COLORS.text_color,
          logo_url: branding.logo_url,
          favicon_url: branding.favicon_url || '',
        });
      } else {
        // No branding settings exist yet, use defaults
        setFormData({
          primary_color: DEFAULT_COLORS.primary_color,
          secondary_color: DEFAULT_COLORS.secondary_color,
          accent_color: DEFAULT_COLORS.accent_color,
          background_color: DEFAULT_COLORS.background_color,
          text_color: DEFAULT_COLORS.text_color,
          logo_url: null,
          favicon_url: '',
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('branding.errors.loadFailed') || 'Failed to load branding settings';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [organizationId, t]);

  /**
   * Validate form fields
   */
  const validateForm = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    // Validate hex color format for all color fields
    const hexColorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;

    if (!hexColorRegex.test(formData.primary_color)) {
      newErrors.primary_color = t('branding.errors.invalidColor') || 'Invalid hex color format (e.g., #3B82F6)';
    }

    if (!hexColorRegex.test(formData.secondary_color)) {
      newErrors.secondary_color = t('branding.errors.invalidColor') || 'Invalid hex color format (e.g., #3B82F6)';
    }

    if (!hexColorRegex.test(formData.accent_color)) {
      newErrors.accent_color = t('branding.errors.invalidColor') || 'Invalid hex color format (e.g., #3B82F6)';
    }

    if (formData.background_color && !hexColorRegex.test(formData.background_color)) {
      newErrors.background_color = t('branding.errors.invalidColor') || 'Invalid hex color format (e.g., #3B82F6)';
    }

    if (formData.text_color && !hexColorRegex.test(formData.text_color)) {
      newErrors.text_color = t('branding.errors.invalidColor') || 'Invalid hex color format (e.g., #3B82F6)';
    }

    // Validate favicon URL if provided
    if (formData.favicon_url && formData.favicon_url.trim()) {
      try {
        new URL(formData.favicon_url.trim());
      } catch {
        newErrors.favicon_url = t('branding.errors.invalidUrl') || 'Invalid URL format';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData, t]);

  /**
   * Handle color field change
   */
  const handleColorChange = useCallback((field: keyof BrandingFormState, value: string) => {
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
   * Handle logo upload complete
   */
  const handleLogoUploadComplete = useCallback((logoUrl: string) => {
    setFormData((prev) => ({
      ...prev,
      logo_url: logoUrl || null,
    }));
    setSuccessMessage(null);
    setError(null);
  }, []);

  /**
   * Handle favicon URL change
   */
  const handleFaviconChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setFormData((prev) => ({
      ...prev,
      favicon_url: value,
    }));

    if (errors.favicon_url) {
      setErrors((prev) => ({
        ...prev,
        favicon_url: undefined,
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
      const updateData: BrandingSettingsUpdate = {
        primary_color: formData.primary_color,
        secondary_color: formData.secondary_color,
        accent_color: formData.accent_color,
        background_color: formData.background_color || undefined,
        text_color: formData.text_color || undefined,
        logo_url: formData.logo_url || undefined,
        favicon_url: formData.favicon_url || undefined,
      };

      if (brandingId) {
        // Update existing branding settings
        await organizationsClient.updateBrandingSettings(brandingId, updateData);
      } else {
        // Create new branding settings
        const newBranding = await organizationsClient.createBrandingSettings({
          organization_id: organizationId,
          ...updateData,
        });
        setBrandingId(newBranding.id);
      }

      setSuccessMessage(t('branding.settings.saveSuccess') || 'Branding settings saved successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('branding.errors.saveFailed') || 'Failed to save branding settings';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  }, [formData, brandingId, organizationId, validateForm, t]);

  /**
   * Handle reset form
   */
  const handleReset = useCallback(() => {
    loadBrandingSettings();
    setSuccessMessage(null);
    setError(null);
    setErrors({});
  }, [loadBrandingSettings]);

  // Load branding settings on mount
  useEffect(() => {
    loadBrandingSettings();
  }, [loadBrandingSettings]);

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
          {t('branding.settings.title') || 'Branding Settings'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('branding.settings.subtitle') || 'Customize your organization\'s visual identity'}
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
                {/* Logo Upload */}
                <Box>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    {t('branding.logo.title') || 'Organization Logo'}
                  </Typography>
                  <LogoUpload
                    organizationId={organizationId}
                    currentLogoUrl={formData.logo_url || undefined}
                    onUploadComplete={handleLogoUploadComplete}
                  />
                </Box>

                <Divider />

                {/* Primary Color */}
                <Box>
                  <ColorPicker
                    id="primary-color"
                    label={t('branding.colors.primary') || 'Primary Color'}
                    value={formData.primary_color}
                    onChange={(color) => handleColorChange('primary_color', color)}
                    helperText={t('branding.colors.primaryHelper') || 'Main brand color for buttons and links'}
                    defaultColor={DEFAULT_COLORS.primary_color}
                    disabled={saving}
                  />
                </Box>

                <Divider />

                {/* Secondary Color */}
                <Box>
                  <ColorPicker
                    id="secondary-color"
                    label={t('branding.colors.secondary') || 'Secondary Color'}
                    value={formData.secondary_color}
                    onChange={(color) => handleColorChange('secondary_color', color)}
                    helperText={t('branding.colors.secondaryHelper') || 'Supporting color for backgrounds and accents'}
                    defaultColor={DEFAULT_COLORS.secondary_color}
                    disabled={saving}
                  />
                </Box>

                <Divider />

                {/* Accent Color */}
                <Box>
                  <ColorPicker
                    id="accent-color"
                    label={t('branding.colors.accent') || 'Accent Color'}
                    value={formData.accent_color}
                    onChange={(color) => handleColorChange('accent_color', color)}
                    helperText={t('branding.colors.accentHelper') || 'Highlight color for notifications and important elements'}
                    defaultColor={DEFAULT_COLORS.accent_color}
                    disabled={saving}
                  />
                </Box>

                <Divider />

                {/* Background Color */}
                <Box>
                  <ColorPicker
                    id="background-color"
                    label={t('branding.colors.background') || 'Background Color'}
                    value={formData.background_color}
                    onChange={(color) => handleColorChange('background_color', color)}
                    helperText={t('branding.colors.backgroundHelper') || 'Optional custom background color'}
                    defaultColor={DEFAULT_COLORS.background_color}
                    disabled={saving}
                    required={false}
                  />
                </Box>

                <Divider />

                {/* Text Color */}
                <Box>
                  <ColorPicker
                    id="text-color"
                    label={t('branding.colors.text') || 'Text Color'}
                    value={formData.text_color}
                    onChange={(color) => handleColorChange('text_color', color)}
                    helperText={t('branding.colors.textHelper') || 'Optional custom text color'}
                    defaultColor={DEFAULT_COLORS.text_color}
                    disabled={saving}
                    required={false}
                  />
                </Box>

                <Divider />

                {/* Favicon URL */}
                <Box>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    {t('branding.favicon.title') || 'Favicon URL'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {t('branding.favicon.helper') || 'Optional URL to your organization\'s favicon'}
                  </Typography>
                  <Box
                    component="input"
                    type="url"
                    value={formData.favicon_url}
                    onChange={handleFaviconChange}
                    disabled={saving}
                    placeholder="https://example.com/favicon.ico"
                    sx={{
                      width: '100%',
                      p: 2,
                      border: '1px solid',
                      borderColor: errors.favicon_url ? 'error.main' : 'divider',
                      borderRadius: 1,
                      fontSize: '0.875rem',
                      '&:focus': {
                        outline: 'none',
                        borderColor: 'primary.main',
                        borderWidth: 2,
                      },
                    }}
                  />
                  {errors.favicon_url && (
                    <Typography variant="caption" color="error" sx={{ mt: 1, display: 'block' }}>
                      {errors.favicon_url}
                    </Typography>
                  )}
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
                    {t('branding.preview.title') || 'Live Preview'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t('branding.preview.subtitle') || 'See how your branding will look'}
                  </Typography>
                </Box>

                <Divider />

                {/* Preview Components */}
                <Stack spacing={2}>
                  {/* Logo Preview */}
                  <Box
                    sx={{
                      p: 2,
                      bgcolor: formData.background_color || 'background.paper',
                      borderRadius: 2,
                      textAlign: 'center',
                    }}
                  >
                    {formData.logo_url ? (
                      <Box
                        component="img"
                        src={formData.logo_url}
                        alt="Logo Preview"
                        sx={{
                          maxWidth: 120,
                          maxHeight: 60,
                          objectFit: 'contain',
                        }}
                      />
                    ) : (
                      <Box
                        sx={{
                          width: 60,
                          height: 60,
                          borderRadius: 2,
                          bgcolor: 'action.hover',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          margin: '0 auto',
                        }}
                      >
                        <BusinessIcon sx={{ fontSize: 32, color: 'action.disabled' }} />
                      </Box>
                    )}
                  </Box>

                  {/* Button Preview */}
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      {t('branding.preview.primaryButton') || 'Primary Button'}
                    </Typography>
                    <Button
                      fullWidth
                      variant="contained"
                      disabled
                      sx={{
                        bgcolor: formData.primary_color,
                        '&:hover': {
                          bgcolor: formData.primary_color,
                          opacity: 0.9,
                        },
                        color: getContrastColor(formData.primary_color),
                      }}
                    >
                      {t('branding.preview.buttonText') || 'Primary Action'}
                    </Button>
                  </Box>

                  {/* Secondary Button Preview */}
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      {t('branding.preview.secondaryButton') || 'Secondary Button'}
                    </Typography>
                    <Button
                      fullWidth
                      variant="outlined"
                      disabled
                      sx={{
                        borderColor: formData.secondary_color,
                        color: formData.secondary_color,
                        '&:hover': {
                          borderColor: formData.secondary_color,
                          bgcolor: `${formData.secondary_color}10`,
                        },
                      }}
                    >
                      {t('branding.preview.buttonText') || 'Secondary Action'}
                    </Button>
                  </Box>

                  {/* Accent Color Preview */}
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      {t('branding.preview.accentColor') || 'Accent Color'}
                    </Typography>
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 1,
                        bgcolor: formData.accent_color,
                        color: getContrastColor(formData.accent_color),
                        textAlign: 'center',
                        fontWeight: 600,
                      }}
                    >
                      {t('branding.preview.accentText') || 'Highlight & Notifications'}
                    </Box>
                  </Box>

                  {/* Text Preview */}
                  <Box>
                    <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                      {t('branding.preview.textColor') || 'Text Color'}
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
                        sx={{ color: formData.text_color }}
                      >
                        {t('branding.preview.textSample') || 'This is how your text will appear'}
                      </Typography>
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
                        {t('branding.preview.infoTitle') || 'Preview'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {t('branding.preview.infoHelper') || 'Changes are reflected in real-time above'}
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

export default BrandingSettings;
