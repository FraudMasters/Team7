import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
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
  FormControlLabel,
  Switch,
  Alert,
  Stack,
  Divider,
  Typography,
  Chip,
  Button,
} from '@mui/material';
import {
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { integrationsClient } from '@/api/integrations';
import type { IntegrationResponse, IntegrationCreate, IntegrationUpdate, IntegrationPlatform } from '@/types/api';

/**
 * Platform-specific credential fields configuration
 */
const PLATFORM_CREDENTIAL_FIELDS: Record<IntegrationPlatform, Array<{ name: string; label: string; type: 'text' | 'password'; required: boolean; helper?: string }>> = {
  workday: [
    { name: 'api_url', label: 'API URL', type: 'text', required: true, helper: 'e.g., https://wd1.workday.com' },
    { name: 'username', label: 'Username', type: 'text', required: true, helper: 'Your Workday username' },
    { name: 'password', label: 'Password', type: 'password', required: true, helper: 'Your Workday password' },
    { name: 'tenant_name', label: 'Tenant Name', type: 'text', required: true, helper: 'Your Workday tenant name' },
  ],
  greenhouse: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, helper: 'Your Greenhouse API key' },
    { name: 'api_url', label: 'API URL', type: 'text', required: false, helper: 'Default: https://harvest.greenhouse.io/v1' },
  ],
  lever: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, helper: 'Your Lever API key' },
    { name: 'api_url', label: 'API URL', type: 'text', required: false, helper: 'Default: https://api.lever.co/v1' },
  ],
  bamboohr: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, helper: 'Your BambooHR API key' },
    { name: 'company_domain', label: 'Company Domain', type: 'text', required: true, helper: 'e.g., companyname.bamboohr.com' },
  ],
  ashby: [
    { name: 'api_key', label: 'API Key', type: 'password', required: true, helper: 'Your Ashby API key' },
    { name: 'api_url', label: 'API URL', type: 'text', required: false, helper: 'Default: https://api.ashbyhq.com' },
  ],
};

/**
 * Platform display configuration
 */
const PLATFORM_CONFIG: Record<IntegrationPlatform, { name: string; category: 'ATS' | 'HRIS'; color: string }> = {
  workday: { name: 'Workday', category: 'HRIS', color: '#f5a623' },
  greenhouse: { name: 'Greenhouse', category: 'ATS', color: '#00a651' },
  lever: { name: 'Lever', category: 'ATS', color: '#00b9f1' },
  bamboohr: { name: 'BambooHR', category: 'HRIS', color: '#e67e22' },
  ashby: { name: 'Ashby', category: 'ATS', color: '#6c5ce7' },
};

/**
 * Form data interface
 */
interface IntegrationFormData {
  name: string;
  platform: IntegrationPlatform | '';
  credentials: Record<string, string>;
  organization_config: Record<string, string>;
  webhook_url: string;
  sync_enabled: boolean;
  sync_interval_minutes: number;
}

/**
 * IntegrationConfig Component Props
 */
interface IntegrationConfigProps {
  /** Integration to edit (null for create mode) */
  integration: IntegrationResponse | null;
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog is closed */
  onClose: () => void;
  /** Callback when integration is saved successfully */
  onSuccess: (integration: IntegrationResponse) => void;
}

/**
 * IntegrationConfig Component
 *
 * Provides a dialog for creating or editing integration configurations.
 * Features include:
 * - Platform selection with dynamic credential fields
 * - Form validation
 * - Test connection functionality
 * - Sync configuration options
 *
 * @example
 * ```tsx
 * <IntegrationConfig
 *   integration={null}
 *   open={open}
 *   onClose={() => setOpen(false)}
 *   onSuccess={(integration) => console.log('Saved:', integration)}
 * />
 * ```
 */
const IntegrationConfig: React.FC<IntegrationConfigProps> = ({
  integration,
  open,
  onClose,
  onSuccess,
}) => {
  const { t } = useTranslation();
  const [submitting, setSubmitting] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  // Form state
  const [formData, setFormData] = useState<IntegrationFormData>({
    name: '',
    platform: '',
    credentials: {},
    organization_config: {},
    webhook_url: '',
    sync_enabled: true,
    sync_interval_minutes: 60,
  });

  /**
   * Initialize form data when editing or opening dialog
   */
  useEffect(() => {
    if (integration) {
      // Edit mode: populate with existing data
      setFormData({
        name: integration.name,
        platform: integration.platform as IntegrationPlatform,
        credentials: integration.credentials as Record<string, string>,
        organization_config: (integration.organization_config as Record<string, string>) || {},
        webhook_url: integration.webhook_url || '',
        sync_enabled: integration.sync_enabled,
        sync_interval_minutes: integration.sync_interval_minutes || 60,
      });
    } else {
      // Create mode: reset form
      setFormData({
        name: '',
        platform: '',
        credentials: {},
        organization_config: {},
        webhook_url: '',
        sync_enabled: true,
        sync_interval_minutes: 60,
      });
    }
    setError(null);
    setTestResult(null);
  }, [integration, open]);

  /**
   * Handle form field changes
   */
  const handleFieldChange = (field: keyof IntegrationFormData, value: string | boolean | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError(null);
    setTestResult(null);
  };

  /**
   * Handle credential field changes
   */
  const handleCredentialChange = (field: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      credentials: { ...prev.credentials, [field]: value },
    }));
    setError(null);
    setTestResult(null);
  };

  /**
   * Handle platform change - reset credentials when platform changes
   */
  const handlePlatformChange = (platform: IntegrationPlatform) => {
    setFormData((prev) => ({
      ...prev,
      platform,
      credentials: {},
      organization_config: {},
    }));
    setError(null);
    setTestResult(null);
  };

  /**
   * Validate form data
   */
  const validateForm = (): string | null => {
    if (!formData.name.trim()) {
      return 'Integration name is required';
    }

    if (!formData.platform) {
      return 'Platform is required';
    }

    const credentialFields = PLATFORM_CREDENTIAL_FIELDS[formData.platform];
    if (credentialFields) {
      for (const field of credentialFields) {
        if (field.required && !formData.credentials[field.name]?.trim()) {
          return `${field.label} is required`;
        }
      }
    }

    if (formData.sync_enabled && (!formData.sync_interval_minutes || formData.sync_interval_minutes < 1)) {
      return 'Sync interval must be at least 1 minute';
    }

    return null;
  };

  /**
   * Test connection to the platform
   */
  const handleTestConnection = async () => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setTestingConnection(true);
    setError(null);
    setTestResult(null);

    try {
      // For create mode, we can't test without creating first
      // So we'll just validate the credentials format
      if (!integration) {
        setTestResult({
          success: true,
          message: 'Credentials format validated. Save integration to test actual connection.',
        });
        return;
      }

      // For edit mode, test the actual connection
      const result = await integrationsClient.testConnection(integration.id);
      setTestResult({
        success: result.success,
        message: result.message,
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Connection test failed';
      setTestResult({
        success: false,
        message,
      });
    } finally {
      setTestingConnection(false);
    }
  };

  /**
   * Handle form submission
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
      // Build credentials object (only include non-empty fields)
      const credentials: Record<string, string> = {};
      Object.entries(formData.credentials).forEach(([key, value]) => {
        if (value && value.trim()) {
          credentials[key] = value.trim();
        }
      });

      // Build organization config (only include non-empty fields)
      const organizationConfig: Record<string, string> = {};
      Object.entries(formData.organization_config).forEach(([key, value]) => {
        if (value && value.trim()) {
          organizationConfig[key] = value.trim();
        }
      });

      if (integration) {
        // Update existing integration
        const updateData: IntegrationUpdate = {
          name: formData.name.trim(),
          credentials: Object.keys(credentials).length > 0 ? credentials : undefined,
          organization_config: Object.keys(organizationConfig).length > 0 ? organizationConfig : undefined,
          webhook_url: formData.webhook_url.trim() || undefined,
          sync_enabled: formData.sync_enabled,
          sync_interval_minutes: formData.sync_interval_minutes,
        };

        const updated = await integrationsClient.updateIntegration(integration.id, updateData);
        onSuccess(updated);
      } else {
        // Create new integration
        const createData: IntegrationCreate = {
          name: formData.name.trim(),
          platform: formData.platform as IntegrationPlatform,
          credentials,
          organization_config: Object.keys(organizationConfig).length > 0 ? organizationConfig : undefined,
          webhook_url: formData.webhook_url.trim() || undefined,
          sync_enabled: formData.sync_enabled,
          sync_interval_minutes: formData.sync_interval_minutes,
        };

        const created = await integrationsClient.createIntegration(createData);
        onSuccess(created);
      }

      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to save integration';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Get credential fields for selected platform
   */
  const getCredentialFields = () => {
    if (!formData.platform) return [];
    return PLATFORM_CREDENTIAL_FIELDS[formData.platform] || [];
  };

  const credentialFields = getCredentialFields();
  const platformConfig = formData.platform ? PLATFORM_CONFIG[formData.platform] : null;

  return (
    <Dialog
      open={open}
      onClose={() => !submitting && !testingConnection && onClose()}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            {integration ? 'Edit Integration' : 'Add Integration'}
          </Typography>
          <IconButton
            onClick={onClose}
            disabled={submitting || testingConnection}
            size="small"
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Basic Information */}
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
              Basic Information
            </Typography>

            <TextField
              label="Integration Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => handleFieldChange('name', e.target.value)}
              placeholder="e.g., Workday Production"
              disabled={submitting}
              sx={{ mb: 2 }}
            />

            <FormControl fullWidth required>
              <InputLabel>Platform</InputLabel>
              <Select
                value={formData.platform}
                label="Platform"
                onChange={(e) => handlePlatformChange(e.target.value as IntegrationPlatform)}
                disabled={submitting || !!integration} // Can't change platform when editing
              >
                {Object.entries(PLATFORM_CONFIG).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        sx={{
                          width: 12,
                          height: 12,
                          borderRadius: '50%',
                          backgroundColor: config.color,
                        }}
                      />
                      <span>{config.name}</span>
                      <Chip
                        label={config.category}
                        size="small"
                        variant="outlined"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {platformConfig && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                Selected platform: {platformConfig.name} ({platformConfig.category})
              </Typography>
            )}
          </Box>

          {/* Credentials Section */}
          {formData.platform && credentialFields.length > 0 && (
            <>
              <Divider />
              <Box>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                  Platform Credentials
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                  Enter the authentication details for {platformConfig?.name}. These credentials are encrypted and stored securely.
                </Typography>

                {credentialFields.map((field) => (
                  <TextField
                    key={field.name}
                    label={field.label}
                    fullWidth
                    required={field.required}
                    type={field.type}
                    value={formData.credentials[field.name] || ''}
                    onChange={(e) => handleCredentialChange(field.name, e.target.value)}
                    placeholder={field.helper}
                    disabled={submitting}
                    helperText={field.helper}
                    sx={{ mb: 2 }}
                  />
                ))}
              </Box>
            </>
          )}

          {/* Sync Configuration */}
          <Divider />
          <Box>
            <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
              Sync Configuration
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={formData.sync_enabled}
                  onChange={(e) => handleFieldChange('sync_enabled', e.target.checked)}
                  disabled={submitting}
                />
              }
              label="Enable automatic synchronization"
              sx={{ mb: 2 }}
            />

            <TextField
              label="Sync Interval (minutes)"
              fullWidth
              type="number"
              value={formData.sync_interval_minutes}
              onChange={(e) => handleFieldChange('sync_interval_minutes', parseInt(e.target.value) || 0)}
              disabled={submitting || !formData.sync_enabled}
              inputProps={{ min: 1, max: 10080 }}
              helperText="How often to sync data (1-10080 minutes)"
              sx={{ mb: 2 }}
            />

            <TextField
              label="Webhook URL (optional)"
              fullWidth
              value={formData.webhook_url}
              onChange={(e) => handleFieldChange('webhook_url', e.target.value)}
              placeholder="https://your-domain.com/webhooks/integrations"
              disabled={submitting}
              helperText="Optional webhook URL for real-time notifications"
            />
          </Box>

          {/* Error Message */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Test Connection Result */}
          {testResult && (
            <Alert
              severity={testResult.success ? 'success' : 'error'}
              icon={testResult.success ? <CheckCircleIcon /> : <ErrorIcon />}
              onClose={() => setTestResult(null)}
            >
              {testResult.message}
            </Alert>
          )}
        </Stack>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={submitting || testingConnection}>
          Cancel
        </Button>
        {formData.platform && (
          <Button
            onClick={handleTestConnection}
            disabled={submitting || testingConnection}
            startIcon={testingConnection ? <CircularProgress size={16} /> : null}
            color="secondary"
          >
            {testingConnection ? 'Testing...' : 'Test Connection'}
          </Button>
        )}
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={submitting || testingConnection}
          startIcon={submitting ? <CircularProgress size={16} /> : null}
        >
          {submitting ? 'Saving...' : integration ? 'Save Changes' : 'Add Integration'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default IntegrationConfig;
