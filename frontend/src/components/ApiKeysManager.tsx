import React, { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Stack,
  Divider,
  Grid,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  VpnKey as VpnKeyIcon,
  Save as SaveIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Cloud as CloudIcon,
} from '@mui/icons-material';
import {
  createApiKey,
  listApiKeys,
  deleteApiKey,
} from '@/api/preferences';
import type {
  ApiKeyResponse,
  ApiKeyCreate,
} from '@/types/api';

/**
 * Form data for creating API keys
 */
interface ApiKeyFormData {
  name: string;
  key: string;
  service: string;
}

/**
 * API keys manager component props
 */
interface ApiKeysManagerProps {
  /** Optional callback when API keys are modified */
  onApiKeyChange?: () => void;
}

/**
 * ApiKeysManager Component
 *
 * Provides a comprehensive interface for managing personal API keys. Features include:
 * - List all stored API keys
 * - Create new API key entries
 * - Delete API keys
 * - Mask/unmask key values for security
 * - Real-time updates with optimistic UI
 *
 * @example
 * ```tsx
 * <ApiKeysManager
 *   onApiKeyChange={() => console.log('API keys changed')}
 * />
 * ```
 */
const ApiKeysManager: React.FC<ApiKeysManagerProps> = ({
  onApiKeyChange,
}) => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKeyResponse[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [keyToDelete, setKeyToDelete] = useState<ApiKeyResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [visibleKeys, setVisibleKeys] = React.useState<Set<string>>(new Set());

  // Form state
  const [formData, setFormData] = useState<ApiKeyFormData>({
    name: '',
    key: '',
    service: '',
  });

  /**
   * Fetch API keys from backend
   */
  const fetchApiKeys = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await listApiKeys();
      setApiKeys(result.api_keys || []);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load API keys';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchApiKeys();
  }, [fetchApiKeys]);

  /**
   * Open create dialog
   */
  const handleCreate = () => {
    setFormData({
      name: '',
      key: '',
      service: '',
    });
    setDialogOpen(true);
  };

  /**
   * Toggle key visibility
   */
  const toggleKeyVisibility = (keyId: string) => {
    setVisibleKeys((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(keyId)) {
        newSet.delete(keyId);
      } else {
        newSet.add(keyId);
      }
      return newSet;
    });
  };

  /**
   * Mask API key for display
   */
  const maskKey = (key: string): string => {
    if (key.length <= 8) {
      return '*'.repeat(key.length);
    }
    return `${key.substring(0, 4)}${'*'.repeat(key.length - 8)}${key.substring(key.length - 4)}`;
  };

  /**
   * Get service icon color based on service name
   */
  const getServiceColor = (service: string): 'success' | 'info' | 'warning' | 'error' => {
    const s = service.toLowerCase();
    if (s.includes('openai') || s.includes('open')) return 'success';
    if (s.includes('anthropic') || s.includes('claude')) return 'info';
    if (s.includes('google') || s.includes('gemini')) return 'warning';
    return 'error';
  };

  /**
   * Open delete confirmation dialog
   */
  const handleDeleteClick = (apiKey: ApiKeyResponse) => {
    setKeyToDelete(apiKey);
    setDeleteDialogOpen(true);
  };

  /**
   * Confirm delete
   */
  const handleDeleteConfirm = async () => {
    if (!keyToDelete) return;

    setSubmitting(true);
    try {
      await deleteApiKey(keyToDelete.id);

      // Optimistic update
      setApiKeys(apiKeys.filter((k) => k.id !== keyToDelete.id));
      setDeleteDialogOpen(false);
      setKeyToDelete(null);

      if (onApiKeyChange) {
        onApiKeyChange();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to delete API key';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Submit form (create)
   */
  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    try {
      const createData: ApiKeyCreate = {
        name: formData.name,
        key: formData.key,
        service: formData.service,
      };

      const created = await createApiKey(createData);
      setApiKeys([created, ...apiKeys]);

      setDialogOpen(false);
      setFormData({
        name: '',
        key: '',
        service: '',
      });

      if (onApiKeyChange) {
        onApiKeyChange();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to create API key';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
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
          Loading API keys...
        </Typography>
      </Box>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Alert
        severity="error"
        action={
          <Button color="inherit" onClick={fetchApiKeys} startIcon={<RefreshIcon />}>
            Try Again
          </Button>
        }
      >
        <AlertTitle>Error</AlertTitle>
        {error}
      </Alert>
    );
  }

  return (
    <Stack spacing={3}>
      {/* Header Section */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" fontWeight={600}>
            API Keys
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchApiKeys}
            size="small"
          >
            Refresh
          </Button>
        </Box>

        <Typography variant="body2" color="text.secondary" paragraph>
          Store your personal API keys for external services like OpenAI, Anthropic, or Google.
          Keys are encrypted and stored securely.
        </Typography>

        {/* Summary Statistics */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6}>
            <Card variant="outlined" sx={{ borderColor: 'primary.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="primary.main" fontWeight={700}>
                  {apiKeys.length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Total API Keys
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Card variant="outlined" sx={{ borderColor: 'success.main' }}>
              <CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h4" color="success.main" fontWeight={700}>
                  {new Set(apiKeys.map((k) => k.service.toLowerCase())).size}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Unique Services
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Create Button */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
            size="large"
          >
            Add API Key
          </Button>
        </Box>
      </Paper>

      {/* API Keys List */}
      {apiKeys.length === 0 ? (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <VpnKeyIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No API keys found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Add your API keys to enable integrations with external services. Click "Add API Key" to get started.
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {apiKeys.map((apiKey) => {
            const isVisible = visibleKeys.has(apiKey.id);
            const serviceColor = getServiceColor(apiKey.service);

            return (
              <Grid item xs={12} key={apiKey.id}>
                <Card
                  variant="outlined"
                  sx={{
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-2px)',
                      boxShadow: 4,
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="h6" fontWeight={600} gutterBottom>
                          {apiKey.name}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 1 }}>
                          <Chip
                            icon={<CloudIcon />}
                            label={apiKey.service}
                            size="small"
                            variant="outlined"
                            color={serviceColor}
                          />
                          <Chip
                            label={`Added: ${new Date(apiKey.created_at).toLocaleDateString()}`}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      </Box>
                      <Stack direction="row" spacing={1}>
                        <Button
                          size="small"
                          onClick={() => toggleKeyVisibility(apiKey.id)}
                          variant="outlined"
                          startIcon={isVisible ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        >
                          {isVisible ? 'Hide' : 'Show'}
                        </Button>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteClick(apiKey)}
                          color="error"
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Stack>
                    </Box>

                    <Divider sx={{ my: 1 }} />

                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                        API Key:
                      </Typography>
                      <Box
                        sx={{
                          p: 1.5,
                          bgcolor: 'action.hover',
                          borderRadius: 1,
                          fontFamily: 'monospace',
                          fontSize: '0.875rem',
                          wordBreak: 'break-all',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                      >
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            userSelect: isVisible ? 'text' : 'none',
                          }}
                        >
                          {isVisible ? apiKey.key : maskKey(apiKey.key)}
                        </Typography>
                        {isVisible && (
                          <Chip
                            label="Visible"
                            size="small"
                            color="warning"
                            sx={{ ml: 1, flexShrink: 0 }}
                          />
                        )}
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Create Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => !submitting && setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              Add API Key
            </Typography>
            <IconButton
              onClick={() => setDialogOpen(false)}
              disabled={submitting}
              size="small"
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Service Name"
              fullWidth
              required
              value={formData.service}
              onChange={(e) => setFormData({ ...formData, service: e.target.value })}
              placeholder="e.g., OpenAI, Anthropic, Google"
              disabled={submitting}
              helperText="The service this API key is for"
            />

            <TextField
              label="Display Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Production OpenAI Key"
              disabled={submitting}
              helperText="A friendly name to identify this key"
            />

            <TextField
              label="API Key"
              fullWidth
              required
              value={formData.key}
              onChange={(e) => setFormData({ ...formData, key: e.target.value })}
              placeholder="e.g., sk-..."
              disabled={submitting}
              helperText="Your actual API key (will be encrypted)"
              type="password"
              autoComplete="off"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <VpnKeyIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={submitting || !formData.name || !formData.key || !formData.service}
            startIcon={submitting ? <CircularProgress size={16} /> : <SaveIcon />}
          >
            {submitting ? 'Adding...' : 'Add Key'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete API Key</DialogTitle>
        <DialogContent>
          <Typography variant="body1">
            Are you sure you want to delete "{keyToDelete?.name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will permanently remove the API key for {keyToDelete?.service}. Any features using this key will stop working.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={submitting}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={submitting}
            startIcon={submitting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            {submitting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
};

export default ApiKeysManager;
