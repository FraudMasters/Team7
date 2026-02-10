/**
 * Create API Key Dialog Component
 *
 * Dialog component for creating new API keys with name, scopes, and rate limits.
 *
 * @module components/developer/CreateAPIKeyDialog
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  Box,
  Typography,
  Alert,
  AlertTitle,
  Chip,
  Divider,
  Stack,
  CircularProgress,
} from '@mui/material';
import {
  VpnKey as VpnKeyIcon,
  Save as SaveIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { apiKeysClient, APIKeyScope, type GenerateAPIKeyRequest } from '@/api/apiKeys';

/**
 * Available scope options grouped by category
 */
const SCOPE_GROUPS = {
  'Candidates': [
    { value: APIKeyScope.ReadCandidates, label: 'Read Candidates', description: 'View candidate data' },
    { value: APIKeyScope.WriteCandidates, label: 'Write Candidates', description: 'Create and modify candidates' },
  ],
  'Vacancies': [
    { value: APIKeyScope.ReadVacancies, label: 'Read Vacancies', description: 'View job postings' },
    { value: APIKeyScope.WriteVacancies, label: 'Write Vacancies', description: 'Create and modify job postings' },
  ],
  'Resumes': [
    { value: APIKeyScope.ReadResumes, label: 'Read Resumes', description: 'View resume data' },
    { value: APIKeyScope.WriteResumes, label: 'Write Resumes', description: 'Upload and modify resumes' },
  ],
  'Webhooks': [
    { value: APIKeyScope.ReadWebhooks, label: 'Read Webhooks', description: 'View webhook subscriptions' },
    { value: APIKeyScope.WriteWebhooks, label: 'Write Webhooks', description: 'Create and modify webhooks' },
  ],
  'Plugins': [
    { value: APIKeyScope.ReadPlugins, label: 'Read Plugins', description: 'View installed plugins' },
    { value: APIKeyScope.WritePlugins, label: 'Write Plugins', description: 'Install and modify plugins' },
  ],
  'Workflows': [
    { value: APIKeyScope.ReadWorkflows, label: 'Read Workflows', description: 'View workflow automations' },
    { value: APIKeyScope.WriteWorkflows, label: 'Write Workflows', description: 'Create and modify workflows' },
  ],
  'Analytics': [
    { value: APIKeyScope.ReadAnalytics, label: 'Read Analytics', description: 'View analytics and metrics' },
  ],
} as const;

interface CreateAPIKeyDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (response: { key: string; message: string }) => void;
}

/**
 * CreateAPIKeyDialog Component
 *
 * Provides a form dialog for creating new API keys with:
 * - Name input
 * - Scope selection (grouped by resource type)
 * - Optional rate limit configuration
 * - Optional expiration date
 *
 * @example
 * ```tsx
 * <CreateAPIKeyDialog
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   onSuccess={(response) => console.log('Key:', response.key)}
 * />
 * ```
 */
const CreateAPIKeyDialog: React.FC<CreateAPIKeyDialogProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [selectedScopes, setSelectedScopes] = useState<Set<string>>(new Set());
  const [rateLimitMinute, setRateLimitMinute] = useState('');
  const [rateLimitHour, setRateLimitHour] = useState('');
  const [rateLimitDay, setRateLimitDay] = useState('');
  const [expiresAt, setExpiresAt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleScopeToggle = (scope: string) => {
    const newScopes = new Set(selectedScopes);
    if (newScopes.has(scope)) {
      newScopes.delete(scope);
    } else {
      newScopes.add(scope);
    }
    setSelectedScopes(newScopes);
  };

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError('Please enter a name for the API key');
      return;
    }

    if (selectedScopes.size === 0) {
      setError('Please select at least one scope');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const request: GenerateAPIKeyRequest = {
        name: name.trim(),
        scopes: Array.from(selectedScopes),
      };

      // Add rate limit if provided
      if (rateLimitMinute || rateLimitHour || rateLimitDay) {
        const rateLimit: Record<string, number> = {};
        if (rateLimitMinute) rateLimit.requests_per_minute = parseInt(rateLimitMinute, 10);
        if (rateLimitHour) rateLimit.requests_per_hour = parseInt(rateLimitHour, 10);
        if (rateLimitDay) rateLimit.requests_per_day = parseInt(rateLimitDay, 10);
        request.rate_limit = rateLimit;
      }

      // Add expiration if provided
      if (expiresAt) {
        request.expires_at = expiresAt;
      }

      const response = await apiKeysClient.generateAPIKey(request);
      onSuccess({ key: response.key, message: response.message });

      // Reset form
      setName('');
      setSelectedScopes(new Set());
      setRateLimitMinute('');
      setRateLimitHour('');
      setRateLimitDay('');
      setExpiresAt('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create API key');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setName('');
      setSelectedScopes(new Set());
      setRateLimitMinute('');
      setRateLimitHour('');
      setRateLimitDay('');
      setExpiresAt('');
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <VpnKeyIcon color="primary" />
          <Typography variant="h6" fontWeight={600}>
            Create New API Key
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Error Alert */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              <AlertTitle>Error</AlertTitle>
              {error}
            </Alert>
          )}

          {/* Warning Alert */}
          <Alert severity="warning">
            <AlertTitle>Important Security Notice</AlertTitle>
            The API key will only be shown once. Make sure to copy and store it securely.
            You won't be able to retrieve it again.
          </Alert>

          {/* Name Input */}
          <TextField
            label="API Key Name"
            fullWidth
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Production Integration Key"
            disabled={loading}
            helperText="A descriptive name to help you identify this key"
          />

          {/* Scopes Selection */}
          <Box>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              Select Scopes
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Choose what this API key can access. Select at least one scope.
            </Typography>

            {Object.entries(SCOPE_GROUPS).map(([groupName, scopes]) => (
              <Box key={groupName} sx={{ mb: 2 }}>
                <Typography
                  variant="subtitle2"
                  color="text.secondary"
                  gutterBottom
                  sx={{ textTransform: 'uppercase', fontSize: '0.75rem', fontWeight: 600 }}
                >
                  {groupName}
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {scopes.map((scope) => (
                    <Chip
                      key={scope.value}
                      label={scope.label}
                      onClick={() => handleScopeToggle(scope.value)}
                      color={selectedScopes.has(scope.value) ? 'primary' : 'default'}
                      variant={selectedScopes.has(scope.value) ? 'filled' : 'outlined'}
                      clickable
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Stack>
              </Box>
            ))}

            {selectedScopes.size > 0 && (
              <Box sx={{ mt: 2 }}>
                <Divider sx={{ mb: 1 }} />
                <Typography variant="caption" color="text.secondary">
                  Selected: {selectedScopes.size} scope{selectedScopes.size !== 1 ? 's' : ''}
                </Typography>
              </Box>
            )}
          </Box>

          {/* Rate Limit Configuration */}
          <Box>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              Rate Limits (Optional)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Set custom rate limits for this API key. Leave empty to use defaults.
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="Requests per Minute"
                type="number"
                value={rateLimitMinute}
                onChange={(e) => setRateLimitMinute(e.target.value)}
                disabled={loading}
                placeholder="60"
                sx={{ flex: 1 }}
                helperText="Maximum API calls per minute"
              />
              <TextField
                label="Requests per Hour"
                type="number"
                value={rateLimitHour}
                onChange={(e) => setRateLimitHour(e.target.value)}
                disabled={loading}
                placeholder="1000"
                sx={{ flex: 1 }}
                helperText="Maximum API calls per hour"
              />
              <TextField
                label="Requests per Day"
                type="number"
                value={rateLimitDay}
                onChange={(e) => setRateLimitDay(e.target.value)}
                disabled={loading}
                placeholder="10000"
                sx={{ flex: 1 }}
                helperText="Maximum API calls per day"
              />
            </Stack>
          </Box>

          {/* Expiration Date */}
          <TextField
            label="Expiration Date (Optional)"
            type="datetime-local"
            fullWidth
            value={expiresAt}
            onChange={(e) => setExpiresAt(e.target.value)}
            disabled={loading}
            InputLabelProps={{ shrink: true }}
            helperText="Leave empty for no expiration"
          />
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} disabled={loading} startIcon={<CloseIcon />}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !name.trim() || selectedScopes.size === 0}
          startIcon={loading ? <CircularProgress size={16} /> : <SaveIcon />}
        >
          {loading ? 'Creating...' : 'Create API Key'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateAPIKeyDialog;
