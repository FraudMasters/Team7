import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Alert,
  AlertTitle,
  Stack,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Grid,
  Card,
  CardContent,
  Chip,
} from '@mui/material';
import {
  Close as CloseIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Edit as EditIcon,
  CloudUpload as CloudUploadIcon,
  VpnKey as VpnKeyIcon,
} from '@mui/icons-material';
import { ssoClient } from '@/api/sso';
import type { SSOProviderItem, SSOProviderCreate, SSOProviderUpdate } from '@/types/api';

/**
 * Form data for SSO provider configuration
 */
interface SSOConfigFormData {
  provider_name: string;
  provider_type: 'okta' | 'azure_ad' | 'google_workspace' | 'generic_saml';
  entity_id: string;
  sso_url: string;
  sls_url: string;
  metadata_url: string;
  x509_certificate: string;
  attribute_mapping_email: string;
  attribute_mapping_name: string;
  attribute_mapping_first_name: string;
  attribute_mapping_last_name: string;
  attribute_mapping_department: string;
  is_enabled: boolean;
}

/**
 * SSO Configuration Form component props
 */
interface SSOConfigFormProps {
  /** Existing provider to edit (undefined for create mode) */
  provider?: SSOProviderItem;
  /** Callback when form is submitted successfully */
  onSuccess?: (provider: SSOProviderItem) => void;
  /** Callback when dialog is closed */
  onClose?: () => void;
  /** Whether the form is in a dialog */
  open?: boolean;
}

/**
 * SSOConfigForm Component
 *
 * Provides a form for creating and editing SAML SSO provider configurations.
 * Supports Okta, Azure AD, Google Workspace, and generic SAML 2.0 providers.
 *
 * Features include:
 * - Provider type selection with pre-filled defaults
 * - Metadata URL fetch support
 * - X.509 certificate input
 * - Attribute mapping configuration
 * - Form validation and error handling
 * - Create and edit modes
 *
 * @example
 * ```tsx
 * // Create new provider
 * <SSOConfigForm
 *   open={true}
 *   onSuccess={(provider) => console.log('Created', provider)}
 *   onClose={() => handleClose()}
 * />
 *
 * // Edit existing provider
 * <SSOConfigForm
 *   provider={existingProvider}
 *   open={true}
 *   onSuccess={(provider) => console.log('Updated', provider)}
 *   onClose={() => handleClose()}
 * />
 * ```
 */
const SSOConfigForm: React.FC<SSOConfigFormProps> = ({
  provider,
  onSuccess,
  onClose,
  open = true,
}) => {
  const { t } = useTranslation();
  const isEditMode = Boolean(provider);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState<SSOConfigFormData>({
    provider_name: '',
    provider_type: 'generic_saml',
    entity_id: '',
    sso_url: '',
    sls_url: '',
    metadata_url: '',
    x509_certificate: '',
    attribute_mapping_email: 'email',
    attribute_mapping_name: 'displayName',
    attribute_mapping_first_name: '',
    attribute_mapping_last_name: '',
    attribute_mapping_department: '',
    is_enabled: true,
  });

  // Initialize form with provider data when editing
  useEffect(() => {
    if (provider) {
      setFormData({
        provider_name: provider.provider_name,
        provider_type: provider.provider_type,
        entity_id: provider.entity_id,
        sso_url: provider.sso_url,
        sls_url: provider.sls_url || '',
        metadata_url: provider.metadata_url || '',
        x509_certificate: '', // Certificate not returned in list view
        attribute_mapping_email: provider.attribute_mapping_email,
        attribute_mapping_name: provider.attribute_mapping_name,
        attribute_mapping_first_name: provider.attribute_mapping_first_name || '',
        attribute_mapping_last_name: provider.attribute_mapping_last_name || '',
        attribute_mapping_department: provider.attribute_mapping_department || '',
        is_enabled: provider.is_enabled,
      });
    }
  }, [provider]);

  /**
   * Handle provider type change with pre-filled defaults
   */
  const handleProviderTypeChange = (providerType: SSOConfigFormData['provider_type']) => {
    setFormData({
      ...formData,
      provider_type: providerType,
      // Set default attribute mappings based on provider
      attribute_mapping_email: providerType === 'azure_ad' ? 'upn' : 'email',
      attribute_mapping_name: providerType === 'azure_ad' ? 'name' : 'displayName',
      attribute_mapping_first_name: providerType === 'azure_ad' ? 'given_name' : 'firstName',
      attribute_mapping_last_name: providerType === 'azure_ad' ? 'family_name' : 'lastName',
      attribute_mapping_department: 'department',
    });
  };

  /**
   * Validate form fields
   */
  const validateForm = (): string | null => {
    if (!formData.provider_name.trim()) {
      return 'Provider name is required';
    }
    if (!formData.entity_id.trim()) {
      return 'Entity ID is required';
    }
    if (!formData.sso_url.trim()) {
      return 'SSO URL is required';
    }
    if (!formData.x509_certificate.trim() && !isEditMode) {
      return 'X.509 Certificate is required';
    }
    if (!formData.attribute_mapping_email.trim()) {
      return 'Email attribute mapping is required';
    }
    if (!formData.attribute_mapping_name.trim()) {
      return 'Name attribute mapping is required';
    }

    // Validate URL formats
    try {
      if (formData.sso_url && !formData.sso_url.startsWith('http')) {
        return 'SSO URL must be a valid URL';
      }
      if (formData.metadata_url && !formData.metadata_url.startsWith('http')) {
        return 'Metadata URL must be a valid URL';
      }
      if (formData.sls_url && !formData.sls_url.startsWith('http')) {
        return 'SLS URL must be a valid URL';
      }
    } catch {
      return 'Invalid URL format';
    }

    return null;
  };

  /**
   * Submit form (create or update)
   */
  const handleSubmit = async () => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      if (isEditMode && provider) {
        // Update existing provider
        const updateData: SSOProviderUpdate = {
          provider_name: formData.provider_name,
          entity_id: formData.entity_id,
          sso_url: formData.sso_url,
          sls_url: formData.sls_url || undefined,
          metadata_url: formData.metadata_url || undefined,
          x509_certificate: formData.x509_certificate || undefined,
          attribute_mapping_email: formData.attribute_mapping_email,
          attribute_mapping_name: formData.attribute_mapping_name,
          attribute_mapping_first_name: formData.attribute_mapping_first_name || undefined,
          attribute_mapping_last_name: formData.attribute_mapping_last_name || undefined,
          attribute_mapping_department: formData.attribute_mapping_department || undefined,
          is_enabled: formData.is_enabled,
        };

        const updated = await ssoClient.updateProvider(provider.id, updateData);
        onSuccess?.(updated);
      } else {
        // Create new provider
        const createData: SSOProviderCreate = {
          provider_name: formData.provider_name,
          provider_type: formData.provider_type,
          entity_id: formData.entity_id,
          sso_url: formData.sso_url,
          sls_url: formData.sls_url || undefined,
          metadata_url: formData.metadata_url || undefined,
          x509_certificate: formData.x509_certificate,
          attribute_mapping_email: formData.attribute_mapping_email,
          attribute_mapping_name: formData.attribute_mapping_name,
          attribute_mapping_first_name: formData.attribute_mapping_first_name || undefined,
          attribute_mapping_last_name: formData.attribute_mapping_last_name || undefined,
          attribute_mapping_department: formData.attribute_mapping_department || undefined,
          is_enabled: formData.is_enabled,
        };

        const created = await ssoClient.createProvider(createData);
        onSuccess?.(created);
      }

      handleClose();
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : isEditMode
          ? 'Failed to update SSO provider'
          : 'Failed to create SSO provider';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Close dialog and reset form
   */
  const handleClose = () => {
    if (!submitting) {
      onClose?.();
    }
  };

  /**
   * Render form content
   */
  const renderFormContent = () => (
    <Stack spacing={3}>
      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)}>
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Basic Configuration Section */}
      <Typography variant="subtitle1" fontWeight={600}>
        Basic Configuration
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField
            label="Provider Name"
            fullWidth
            required
            value={formData.provider_name}
            onChange={(e) => setFormData({ ...formData, provider_name: e.target.value })}
            placeholder="e.g., Okta Production"
            disabled={submitting}
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <FormControl fullWidth required>
            <InputLabel>Provider Type</InputLabel>
            <Select
              value={formData.provider_type}
              label="Provider Type"
              onChange={(e) =>
                handleProviderTypeChange(
                  e.target.value as SSOConfigFormData['provider_type']
                )
              }
              disabled={submitting}
            >
              <MenuItem value="okta">
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip label="Okta" size="small" color="primary" />
                </Stack>
              </MenuItem>
              <MenuItem value="azure_ad">
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip label="Azure AD" size="small" color="info" />
                </Stack>
              </MenuItem>
              <MenuItem value="google_workspace">
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip label="Google Workspace" size="small" color="success" />
                </Stack>
              </MenuItem>
              <MenuItem value="generic_saml">
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip label="Generic SAML" size="small" color="default" />
                </Stack>
              </MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* SAML Configuration Section */}
      <Divider />
      <Typography variant="subtitle1" fontWeight={600}>
        SAML Configuration
      </Typography>

      <TextField
        label="Entity ID"
        fullWidth
        required
        value={formData.entity_id}
        onChange={(e) => setFormData({ ...formData, entity_id: e.target.value })}
        placeholder="https://sso.example.com/entity-id"
        disabled={submitting}
        helperText="The unique identifier for this SSO provider"
      />

      <TextField
        label="SSO URL (Single Sign-On)"
        fullWidth
        required
        value={formData.sso_url}
        onChange={(e) => setFormData({ ...formData, sso_url: e.target.value })}
        placeholder="https://sso.example.com/sso"
        disabled={submitting}
        helperText="The IdP's SSO endpoint URL"
      />

      <TextField
        label="SLS URL (Single Logout)"
        fullWidth
        value={formData.sls_url}
        onChange={(e) => setFormData({ ...formData, sls_url: e.target.value })}
        placeholder="https://sso.example.com/sls"
        disabled={submitting}
        helperText="Optional: The IdP's SLO endpoint URL"
      />

      <TextField
        label="Metadata URL"
        fullWidth
        value={formData.metadata_url}
        onChange={(e) => setFormData({ ...formData, metadata_url: e.target.value })}
        placeholder="https://sso.example.com/metadata"
        disabled={submitting}
        helperText="Optional: URL to fetch SAML metadata automatically"
      />

      <TextField
        label="X.509 Certificate"
        fullWidth
        required={!isEditMode}
        multiline
        rows={6}
        value={formData.x509_certificate}
        onChange={(e) => setFormData({ ...formData, x509_certificate: e.target.value })}
        placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----"
        disabled={submitting}
        helperText={
          isEditMode
            ? 'Leave empty to keep existing certificate'
            : 'The IdP\'s X.509 certificate for verifying SAML responses'
        }
      />

      {/* Attribute Mapping Section */}
      <Divider />
      <Typography variant="subtitle1" fontWeight={600}>
        Attribute Mapping
      </Typography>
      <Typography variant="caption" color="text.secondary">
        Map SAML attributes to user profile fields
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField
            label="Email Attribute"
            fullWidth
            required
            value={formData.attribute_mapping_email}
            onChange={(e) =>
              setFormData({ ...formData, attribute_mapping_email: e.target.value })
            }
            placeholder="email"
            disabled={submitting}
            helperText="SAML attribute for user email"
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            label="Name Attribute"
            fullWidth
            required
            value={formData.attribute_mapping_name}
            onChange={(e) =>
              setFormData({ ...formData, attribute_mapping_name: e.target.value })
            }
            placeholder="displayName"
            disabled={submitting}
            helperText="SAML attribute for full name"
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            label="First Name Attribute"
            fullWidth
            value={formData.attribute_mapping_first_name}
            onChange={(e) =>
              setFormData({ ...formData, attribute_mapping_first_name: e.target.value })
            }
            placeholder="firstName"
            disabled={submitting}
            helperText="Optional: SAML attribute for first name"
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            label="Last Name Attribute"
            fullWidth
            value={formData.attribute_mapping_last_name}
            onChange={(e) =>
              setFormData({ ...formData, attribute_mapping_last_name: e.target.value })
            }
            placeholder="lastName"
            disabled={submitting}
            helperText="Optional: SAML attribute for last name"
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <TextField
            label="Department Attribute"
            fullWidth
            value={formData.attribute_mapping_department}
            onChange={(e) =>
              setFormData({ ...formData, attribute_mapping_department: e.target.value })
            }
            placeholder="department"
            disabled={submitting}
            helperText="Optional: SAML attribute for department"
          />
        </Grid>

        <Grid item xs={12} sm={6}>
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              value={formData.isEnabled ? 'enabled' : 'disabled'}
              label="Status"
              onChange={(e) =>
                setFormData({ ...formData, is_enabled: e.target.value === 'enabled' })
              }
              disabled={submitting}
            >
              <MenuItem value="enabled">Enabled</MenuItem>
              <MenuItem value="disabled">Disabled</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* Info Alert */}
      <Alert severity="info">
        <AlertTitle>Configuration Help</AlertTitle>
        For detailed setup instructions, refer to your SSO provider's documentation.
        Common values:
        <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
          <li>Okta: email, displayName, firstName, lastName</li>
          <li>Azure AD: upn, name, given_name, family_name</li>
          <li>Google: email, name, firstName, lastName</li>
        </ul>
      </Alert>
    </Stack>
  );

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: 600 },
      }}
    >
      <DialogTitle>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Stack direction="row" spacing={2} alignItems="center">
            <VpnKeyIcon color="primary" />
            <Typography variant="h6">
              {isEditMode ? 'Edit SSO Configuration' : 'Add SSO Configuration'}
            </Typography>
          </Stack>
          <IconButton
            onClick={handleClose}
            disabled={submitting}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ mt: 2 }}>{renderFormContent()}</Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} disabled={submitting}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={submitting}
          startIcon={submitting ? <CircularProgress size={16} /> : <SaveIcon />}
        >
          {submitting ? 'Saving...' : isEditMode ? 'Update Provider' : 'Create Provider'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SSOConfigForm;
