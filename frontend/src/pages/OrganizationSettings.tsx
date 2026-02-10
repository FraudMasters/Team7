import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Container,
  Typography,
  Box,
  Paper,
  TextField,
  Button,
  Alert,
  Stack,
  Divider,
  Switch,
  FormControlLabel,
  CircularProgress,
} from '@mui/material';
import {
  Save as SaveIcon,
  Business as BusinessIcon,
} from '@mui/icons-material';
import { organizationsClient } from '@/api/organizations';
import type { OrganizationResponse, OrganizationUpdate } from '@/types';

/**
 * Form state interface
 */
interface OrganizationFormState {
  name: string;
  slug: string;
  domain: string;
  logo_url: string;
  is_active: boolean;
}

/**
 * Form validation errors interface
 */
interface FormErrors {
  name?: string;
  slug?: string;
  domain?: string;
  logo_url?: string;
}

/**
 * Organization Settings Page
 *
 * Provides an interface for managing organization details:
 * - Organization name and slug
 * - Domain configuration
 * - Logo URL
 * - Active status
 *
 * Accessible at /organization-settings
 *
 * @example
 * ```tsx
 * // Route configuration in App.tsx
 * <Route path="/organization-settings" element={<OrganizationSettings />} />
 * ```
 */
const OrganizationSettings: React.FC = () => {
  const { t } = useTranslation();

  // Form state
  const [organizationId, setOrganizationId] = useState<string>('org123'); // In production, from auth context
  const [formData, setFormData] = useState<OrganizationFormState>({
    name: '',
    slug: '',
    domain: '',
    logo_url: '',
    is_active: true,
  });

  // UI state
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<FormErrors>({});

  /**
   * Load organization data
   */
  const loadOrganization = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const org = await organizationsClient.getOrganization(organizationId);
      setFormData({
        name: org.name,
        slug: org.slug,
        domain: org.domain || '',
        logo_url: org.logo_url || '',
        is_active: org.is_active,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('organization.errors.loadFailed');
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

    // Name validation
    if (!formData.name.trim()) {
      newErrors.name = t('validation.required', { field: t('organization.name') }) || 'Organization name is required';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = t('validation.minLength', { field: t('organization.name'), min: 2 }) || 'Organization name must be at least 2 characters';
    } else if (formData.name.trim().length > 100) {
      newErrors.name = t('validation.maxLength', { field: t('organization.name'), max: 100 }) || 'Organization name must not exceed 100 characters';
    }

    // Slug validation
    if (!formData.slug.trim()) {
      newErrors.slug = t('validation.required', { field: t('organization.slug') }) || 'Slug is required';
    } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug = t('organization.errors.slugFormat') || 'Slug must contain only lowercase letters, numbers, and hyphens';
    } else if (formData.slug.trim().length < 2) {
      newErrors.slug = t('validation.minLength', { field: t('organization.slug'), min: 2 }) || 'Slug must be at least 2 characters';
    } else if (formData.slug.trim().length > 50) {
      newErrors.slug = t('validation.maxLength', { field: t('organization.slug'), max: 50 }) || 'Slug must not exceed 50 characters';
    }

    // Domain validation (optional but must be valid if provided)
    if (formData.domain && formData.domain.trim()) {
      const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$/;
      if (!domainRegex.test(formData.domain.trim())) {
        newErrors.domain = t('organization.errors.invalidDomain') || 'Invalid domain format (e.g., example.com)';
      }
    }

    // Logo URL validation (optional but must be valid URL if provided)
    if (formData.logo_url && formData.logo_url.trim()) {
      try {
        new URL(formData.logo_url.trim());
      } catch {
        newErrors.logo_url = t('organization.errors.invalidUrl') || 'Invalid URL format';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData, t]);

  /**
   * Handle form field change
   */
  const handleFieldChange = useCallback((field: keyof OrganizationFormState, value: string | boolean) => {
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
   * Handle slug generation from name
   */
  const handleNameBlur = useCallback(() => {
    if (formData.name && !formData.slug) {
      const slug = formData.name
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
      handleFieldChange('slug', slug);
    }
  }, [formData.name, formData.slug, handleFieldChange]);

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
      const updateData: OrganizationUpdate = {
        name: formData.name.trim(),
        slug: formData.slug.trim(),
        domain: formData.domain.trim() || undefined,
        logo_url: formData.logo_url.trim() || undefined,
        is_active: formData.is_active,
      };

      await organizationsClient.updateOrganization(organizationId, updateData);

      setSuccessMessage(t('organization.settings.saveSuccess') || 'Organization settings saved successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : t('organization.errors.saveFailed');
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  }, [formData, organizationId, validateForm, t]);

  /**
   * Handle reset form
   */
  const handleReset = useCallback(() => {
    loadOrganization();
    setSuccessMessage(null);
    setError(null);
    setErrors({});
  }, [loadOrganization]);

  // Load organization data on mount
  useEffect(() => {
    loadOrganization();
  }, [loadOrganization]);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {t('organization.settings.title') || 'Organization Settings'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {t('organization.settings.subtitle') || 'Manage your organization details and configuration'}
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

      {/* Form */}
      {!loading && (
        <Paper component="form" onSubmit={handleSubmit} sx={{ p: 4 }}>
          <Stack spacing={4}>
            {/* Organization Name */}
            <Box>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                {t('organization.name') || 'Organization Name'}
                <span style={{ color: 'red' }}> *</span>
              </Typography>
              <TextField
                fullWidth
                value={formData.name}
                onChange={(e) => handleFieldChange('name', e.target.value)}
                onBlur={handleNameBlur}
                error={!!errors.name}
                helperText={errors.name || (t('organization.settings.nameHelper') || 'The official name of your organization (2-100 characters)')}
                placeholder={t('organization.settings.namePlaceholder') || 'Acme Corporation'}
                disabled={saving}
                inputProps={{ maxLength: 100 }}
              />
            </Box>

            <Divider />

            {/* Slug */}
            <Box>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                {t('organization.slug') || 'Slug'}
                <span style={{ color: 'red' }}> *</span>
              </Typography>
              <TextField
                fullWidth
                value={formData.slug}
                onChange={(e) => handleFieldChange('slug', e.target.value.toLowerCase())}
                error={!!errors.slug}
                helperText={errors.slug || (t('organization.settings.slugHelper') || 'Unique identifier used in URLs. Lowercase letters, numbers, and hyphens only (2-50 characters)')}
                placeholder={t('organization.settings.slugPlaceholder') || 'acme-corporation'}
                disabled={saving}
                inputProps={{ maxLength: 50 }}
              />
            </Box>

            <Divider />

            {/* Domain */}
            <Box>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                {t('organization.domain') || 'Domain'}
              </Typography>
              <TextField
                fullWidth
                value={formData.domain}
                onChange={(e) => handleFieldChange('domain', e.target.value)}
                error={!!errors.domain}
                helperText={errors.domain || (t('organization.settings.domainHelper') || 'Optional domain for SSO (e.g., example.com)')}
                placeholder={t('organization.settings.domainPlaceholder') || 'example.com'}
                disabled={saving}
              />
            </Box>

            <Divider />

            {/* Logo URL */}
            <Box>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                {t('organization.logoUrl') || 'Logo URL'}
              </Typography>
              <TextField
                fullWidth
                value={formData.logo_url}
                onChange={(e) => handleFieldChange('logo_url', e.target.value)}
                error={!!errors.logo_url}
                helperText={errors.logo_url || (t('organization.settings.logoUrlHelper') || 'Optional: URL to your organization logo image')}
                placeholder={t('organization.settings.logoUrlPlaceholder') || 'https://example.com/logo.png'}
                disabled={saving}
              />
            </Box>

            <Divider />

            {/* Active Status */}
            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => handleFieldChange('is_active', e.target.checked)}
                    disabled={saving}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="subtitle1" fontWeight={600}>
                      {t('organization.active') || 'Active Organization'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {t('organization.settings.activeHelper') || 'When disabled, the organization will not be accessible to users'}
                    </Typography>
                  </Box>
                }
              />
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
      )}

      {/* Info Box */}
      {!loading && (
        <Box sx={{ mt: 3 }}>
          <Paper sx={{ p: 3, bgcolor: 'info.main', bgcolorOpacity: 0.1 }}>
            <Stack direction="row" spacing={2} alignItems="flex-start">
              <BusinessIcon color="info" sx={{ mt: 0.5 }} />
              <Box>
                <Typography variant="subtitle2" fontWeight={600} color="info.dark">
                  {t('organization.settings.infoTitle') || 'Organization ID'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {organizationId}
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {t('organization.settings.infoHelper') || 'This is your unique organization identifier. It is used internally by the system.'}
                </Typography>
              </Box>
            </Stack>
          </Paper>
        </Box>
      )}
    </Container>
  );
};

export default OrganizationSettings;
