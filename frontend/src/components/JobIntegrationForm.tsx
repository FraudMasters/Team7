/**
 * Job Integration Form Component
 *
 * Form component for adding and editing job board integrations.
 * Supports Indeed, ZipRecruiter, Glassdoor, and custom webhook integrations.
 */

import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress,
  Grid2,
  Paper,
} from '@mui/material';
import {
  Save as SaveIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { jobIntegrationsClient } from '../api/jobIntegrations';
import type { JobBoardIntegrationResponse, JobBoardIntegrationCreate, JobBoardIntegrationUpdate } from '../types/api';

interface JobIntegrationFormProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  integration?: JobBoardIntegrationResponse | null;
}

export function JobIntegrationForm({
  open,
  onClose,
  onSuccess,
  integration,
}: JobIntegrationFormProps) {
  const isEditMode = Boolean(integration);

  const [name, setName] = useState('');
  const [apiEndpoint, setApiEndpoint] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [configJson, setConfigJson] = useState('');
  const [configError, setConfigError] = useState('');

  // Reset form when dialog opens/closes or integration changes
  useEffect(() => {
    if (open) {
      if (integration) {
        setName(integration.name);
        setApiEndpoint(integration.api_endpoint);
        setApiKey(integration.api_key);
        setEnabled(integration.enabled);
        setConfigJson(
          integration.config && Object.keys(integration.config).length > 0
            ? JSON.stringify(integration.config, null, 2)
            : ''
        );
      } else {
        resetForm();
      }
      setConfigError('');
    }
  }, [open, integration]);

  const resetForm = () => {
    setName('');
    setApiEndpoint('');
    setApiKey('');
    setEnabled(true);
    setConfigJson('');
    setConfigError('');
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const validateConfig = (jsonStr: string): boolean => {
    if (!jsonStr.trim()) {
      setConfigError('');
      return true;
    }
    try {
      JSON.parse(jsonStr);
      setConfigError('');
      return true;
    } catch {
      setConfigError('Invalid JSON format');
      return false;
    }
  };

  const handleConfigChange = (value: string) => {
    setConfigJson(value);
    if (value.trim()) {
      validateConfig(value);
    } else {
      setConfigError('');
    }
  };

  // Create integration mutation
  const createMutation = useMutation({
    mutationFn: async (data: JobBoardIntegrationCreate) => {
      return await jobIntegrationsClient.createIntegration(data);
    },
    onSuccess: () => {
      onSuccess();
      handleClose();
    },
  });

  // Update integration mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: JobBoardIntegrationUpdate }) => {
      return await jobIntegrationsClient.updateIntegration(id, data);
    },
    onSuccess: () => {
      onSuccess();
      handleClose();
    },
  });

  const handleSubmit = () => {
    // Validate required fields
    if (!name.trim()) {
      return;
    }
    if (!apiEndpoint.trim()) {
      return;
    }

    // Validate config JSON if provided
    if (configJson.trim() && !validateConfig(configJson)) {
      return;
    }

    const parsedConfig = configJson.trim() ? JSON.parse(configJson) : undefined;

    if (isEditMode && integration) {
      updateMutation.mutate({
        id: integration.id,
        data: {
          name: name.trim(),
          api_endpoint: apiEndpoint.trim(),
          api_key: apiKey.trim(),
          enabled,
          config: parsedConfig,
        },
      });
    } else {
      createMutation.mutate({
        name: name.trim(),
        api_endpoint: apiEndpoint.trim(),
        api_key: apiKey.trim(),
        enabled,
        config: parsedConfig,
      });
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;
  const hasError = createMutation.error || updateMutation.error;
  const errorMessage = hasError
    ? ((createMutation.error || updateMutation.error) as { detail?: string }).detail ||
      'An error occurred while saving the integration.'
    : null;

  const isValid = name.trim() && apiEndpoint.trim() && !configError;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>{isEditMode ? 'Edit Integration' : 'Add Integration'}</DialogTitle>

      <DialogContent>
        {/* Error Alert */}
        {errorMessage && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {errorMessage}
          </Alert>
        )}

        {/* Integration Name */}
        <TextField
          autoFocus
          fullWidth
          label="Integration Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          sx={{ mt: 2 }}
          placeholder="e.g., Indeed, ZipRecruiter, Custom Webhook"
          slotProps={{
            input: {
              'aria-label': 'Integration name',
            },
          }}
          disabled={isPending}
        />

        {/* API Endpoint */}
        <TextField
          fullWidth
          label="API Endpoint"
          value={apiEndpoint}
          onChange={(e) => setApiEndpoint(e.target.value)}
          sx={{ mt: 2 }}
          placeholder="https://api.example.com/v1"
          slotProps={{
            input: {
              'aria-label': 'API endpoint',
            },
          }}
          disabled={isPending}
        />

        {/* API Key */}
        <TextField
          fullWidth
          label="API Key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          sx={{ mt: 2 }}
          type="password"
          placeholder="Your API key"
          slotProps={{
            input: {
              'aria-label': 'API key',
            },
          }}
          disabled={isPending}
        />

        {/* Configuration (JSON) */}
        <Typography variant="subtitle2" sx={{ mt: 3, mb: 1 }}>
          Configuration (Optional JSON)
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={4}
          label="Additional Configuration"
          value={configJson}
          onChange={(e) => handleConfigChange(e.target.value)}
          placeholder='{"polling_interval": 3600, "webhook_url": "https://..."}'
          slotProps={{
            input: {
              'aria-label': 'Integration configuration',
            },
          }}
          disabled={isPending}
          error={Boolean(configError)}
          helperText={configError || 'Optional JSON configuration for advanced settings'}
          sx={{
            fontFamily: 'monospace',
            fontSize: '0.875rem',
          }}
        />

        {/* Enabled Toggle */}
        <FormControlLabel
          control={
            <Switch
              checked={enabled}
              onChange={(e) => setEnabled(e.target.checked)}
              aria-label="Enable integration"
              disabled={isPending}
            />
          }
          label="Enable integration"
          sx={{ mt: 2 }}
        />

        {/* Info Box */}
        <Paper
          variant="outlined"
          sx={{
            mt: 3,
            p: 2,
            bgcolor: 'info.main',
            bgcolorOpacity: 0.05,
            borderColor: 'info.main',
            borderColorOpacity: 0.3,
          }}
        >
          <Typography variant="caption" color="text.secondary">
            <strong>Supported Integrations:</strong>
            <br />• Indeed - Use API endpoint: https://api.indeed.com/v2
            <br />• ZipRecruiter - Use API endpoint: https://api.ziprecruiter.com
            <br />• Glassdoor - Use API endpoint: https://api.glassdoor.com/api
            <br />• Custom Webhooks - Use your custom webhook endpoint
          </Typography>
        </Paper>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={isPending}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          startIcon={isPending ? <CircularProgress size={16} /> : <SaveIcon />}
          disabled={!isValid || isPending}
        >
          {isEditMode ? 'Save' : 'Add'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default JobIntegrationForm;
